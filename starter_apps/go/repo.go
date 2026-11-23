package main

import (
	"context"
	"embed"
	"fmt"
	"io/fs"
	"sort"
	"sync"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Item es lo que se guarda y se devuelve en la API.
type Item struct {
	ID       int64  `json:"id"`
	Name     string `json:"name"`
	Quantity int    `json:"quantity"`
}

// Repo guarda items: Postgres si hay DATABASE_URL, memoria si no.
type Repo interface {
	Add(ctx context.Context, name string, quantity int) (Item, error)
	List(ctx context.Context) ([]Item, error)
}

type memRepo struct {
	mu    sync.Mutex
	items []Item
}

func newMemRepo() *memRepo { return &memRepo{items: []Item{}} }

func (m *memRepo) Add(_ context.Context, name string, quantity int) (Item, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	item := Item{ID: int64(len(m.items) + 1), Name: name, Quantity: quantity}
	m.items = append(m.items, item)
	return item, nil
}

func (m *memRepo) List(_ context.Context) ([]Item, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	return append([]Item{}, m.items...), nil
}

//go:embed migrations/*.sql
var migrations embed.FS

type pgRepo struct{ pool *pgxpool.Pool }

func newPgRepo(ctx context.Context, url string) (*pgRepo, error) {
	pool, err := pgxpool.New(ctx, url)
	if err != nil {
		return nil, err
	}
	r := &pgRepo{pool: pool}
	if err := r.migrate(ctx); err != nil {
		pool.Close()
		return nil, err
	}
	return r, nil
}

// migrate aplica migrations/*.sql en orden, una sola vez cada una. El lock evita carreras entre replicas.
func (r *pgRepo) migrate(ctx context.Context) error {
	names, err := fs.Glob(migrations, "migrations/*.sql")
	if err != nil {
		return err
	}
	sort.Strings(names)
	return pgx.BeginFunc(ctx, r.pool, func(tx pgx.Tx) error {
		if _, err := tx.Exec(ctx, "SELECT pg_advisory_xact_lock(727274)"); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, "CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)"); err != nil {
			return err
		}
		for _, path := range names {
			name := path[len("migrations/"):]
			var done bool
			if err := tx.QueryRow(ctx, "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE name = $1)", name).Scan(&done); err != nil {
				return err
			}
			if done {
				continue
			}
			sql, err := migrations.ReadFile(path)
			if err != nil {
				return err
			}
			if _, err := tx.Exec(ctx, string(sql)); err != nil {
				return fmt.Errorf("migracion %s: %w", name, err)
			}
			if _, err := tx.Exec(ctx, "INSERT INTO schema_migrations (name) VALUES ($1)", name); err != nil {
				return err
			}
		}
		return nil
	})
}

func (r *pgRepo) Add(ctx context.Context, name string, quantity int) (Item, error) {
	var item Item
	err := r.pool.QueryRow(ctx,
		"INSERT INTO items (name, quantity) VALUES ($1, $2) RETURNING id, name, quantity",
		name, quantity).Scan(&item.ID, &item.Name, &item.Quantity)
	return item, err
}

func (r *pgRepo) List(ctx context.Context) ([]Item, error) {
	rows, err := r.pool.Query(ctx, "SELECT id, name, quantity FROM items ORDER BY id")
	if err != nil {
		return nil, err
	}
	return pgx.CollectRows(rows, pgx.RowToStructByPos[Item])
}

func (r *pgRepo) Close() { r.pool.Close() }

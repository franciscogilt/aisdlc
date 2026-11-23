package main

import (
	"context"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
)

// backends devuelve memoria siempre y Postgres si hay DATABASE_URL.
func backends(t *testing.T) map[string]Repo {
	t.Helper()
	out := map[string]Repo{"memoria": newMemRepo()}
	if url := os.Getenv("DATABASE_URL"); url != "" {
		pg, err := newPgRepo(context.Background(), url)
		if err != nil {
			t.Fatalf("postgres: %v", err)
		}
		t.Cleanup(pg.Close)
		out["postgres"] = pg
	}
	return out
}

func do(t *testing.T, repo Repo, method, path, body string) *httptest.ResponseRecorder {
	t.Helper()
	req := httptest.NewRequest(method, path, strings.NewReader(body))
	rec := httptest.NewRecorder()
	newMux(repo).ServeHTTP(rec, req)
	return rec
}

func TestHealth(t *testing.T) {
	rec := do(t, newMemRepo(), http.MethodGet, "/health", "")
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d", rec.Code)
	}
	if !strings.Contains(rec.Body.String(), `"status":"ok"`) {
		t.Fatalf("body = %s", rec.Body)
	}
}

func TestCreateAndListItems(t *testing.T) {
	for name, repo := range backends(t) {
		t.Run(name, func(t *testing.T) {
			rec := do(t, repo, http.MethodPost, "/items", `{"name":"cafe","quantity":2}`)
			if rec.Code != http.StatusCreated {
				t.Fatalf("status = %d", rec.Code)
			}
			if !strings.Contains(rec.Body.String(), `"name":"cafe"`) {
				t.Fatalf("body = %s", rec.Body)
			}
			list := do(t, repo, http.MethodGet, "/items", "")
			if list.Code != http.StatusOK || !strings.Contains(list.Body.String(), `"name":"cafe"`) {
				t.Fatalf("list = %d %s", list.Code, list.Body)
			}
		})
	}
}

func TestMigrationsAreIdempotent(t *testing.T) {
	url := os.Getenv("DATABASE_URL")
	if url == "" {
		t.Skip("sin DATABASE_URL")
	}
	for range 2 {
		pg, err := newPgRepo(context.Background(), url)
		if err != nil {
			t.Fatal(err)
		}
		pg.Close()
	}
}

func TestRejectsInvalidQuantity(t *testing.T) {
	if rec := do(t, newMemRepo(), http.MethodPost, "/items", `{"name":"cafe","quantity":0}`); rec.Code != http.StatusUnprocessableEntity {
		t.Fatalf("status = %d", rec.Code)
	}
}

func TestRejectsInvalidJSON(t *testing.T) {
	if rec := do(t, newMemRepo(), http.MethodPost, "/items", "no-json"); rec.Code != http.StatusBadRequest {
		t.Fatalf("status = %d", rec.Code)
	}
}

func TestWrongMethod(t *testing.T) {
	if rec := do(t, newMemRepo(), http.MethodDelete, "/items", ""); rec.Code != http.StatusMethodNotAllowed {
		t.Fatalf("status = %d", rec.Code)
	}
}

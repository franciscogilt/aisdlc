package main

import (
	"context"
	"log/slog"
	"net/http"
	"os"
	"time"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	var repo Repo = newMemRepo()
	if url := os.Getenv("DATABASE_URL"); url != "" {
		pg, err := newPgRepo(context.Background(), url)
		if err != nil {
			slog.Error("no se pudo conectar o migrar la base de datos", "error", err)
			os.Exit(1)
		}
		defer pg.Close()
		repo = pg
	}
	srv := &http.Server{
		Addr:              ":" + port,
		Handler:           newMux(repo),
		ReadHeaderTimeout: 5 * time.Second,
	}
	slog.Info("escuchando", "addr", srv.Addr)
	if err := srv.ListenAndServe(); err != nil {
		slog.Error("el servidor se detuvo", "error", err)
		os.Exit(1)
	}
}

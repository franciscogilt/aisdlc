package main

import (
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
	srv := &http.Server{
		Addr:              ":" + port,
		Handler:           newMux(),
		ReadHeaderTimeout: 5 * time.Second,
	}
	slog.Info("escuchando", "addr", srv.Addr)
	if err := srv.ListenAndServe(); err != nil {
		slog.Error("el servidor se detuvo", "error", err)
		os.Exit(1)
	}
}

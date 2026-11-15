package main

import (
	"encoding/json"
	"net/http"
)

type itemIn struct {
	Name     string `json:"name"`
	Quantity int    `json:"quantity"`
}

func writeJSON(w http.ResponseWriter, status int, body any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(body)
}

func newMux() *http.ServeMux {
	mux := http.NewServeMux()

	mux.HandleFunc("GET /health", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	})

	mux.HandleFunc("POST /items", func(w http.ResponseWriter, r *http.Request) {
		r.Body = http.MaxBytesReader(w, r.Body, 100<<10)
		var item itemIn
		if err := json.NewDecoder(r.Body).Decode(&item); err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": "JSON invalido"})
			return
		}
		errs := map[string]string{}
		if len(item.Name) < 1 || len(item.Name) > 80 {
			errs["name"] = "texto de 1 a 80 caracteres"
		}
		if item.Quantity < 1 || item.Quantity > 1000 {
			errs["quantity"] = "entero de 1 a 1000"
		}
		if len(errs) > 0 {
			writeJSON(w, http.StatusUnprocessableEntity, map[string]any{"errors": errs})
			return
		}
		writeJSON(w, http.StatusCreated, item)
	})

	return mux
}

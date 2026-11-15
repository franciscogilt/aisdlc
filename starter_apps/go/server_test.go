package main

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func do(t *testing.T, method, path, body string) *httptest.ResponseRecorder {
	t.Helper()
	req := httptest.NewRequest(method, path, strings.NewReader(body))
	rec := httptest.NewRecorder()
	newMux().ServeHTTP(rec, req)
	return rec
}

func TestHealth(t *testing.T) {
	rec := do(t, http.MethodGet, "/health", "")
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d", rec.Code)
	}
	if !strings.Contains(rec.Body.String(), `"status":"ok"`) {
		t.Fatalf("body = %s", rec.Body)
	}
}

func TestCreateItem(t *testing.T) {
	rec := do(t, http.MethodPost, "/items", `{"name":"cafe","quantity":2}`)
	if rec.Code != http.StatusCreated {
		t.Fatalf("status = %d", rec.Code)
	}
	if !strings.Contains(rec.Body.String(), `"name":"cafe"`) {
		t.Fatalf("body = %s", rec.Body)
	}
}

func TestRejectsInvalidQuantity(t *testing.T) {
	if rec := do(t, http.MethodPost, "/items", `{"name":"cafe","quantity":0}`); rec.Code != http.StatusUnprocessableEntity {
		t.Fatalf("status = %d", rec.Code)
	}
}

func TestRejectsInvalidJSON(t *testing.T) {
	if rec := do(t, http.MethodPost, "/items", "no-json"); rec.Code != http.StatusBadRequest {
		t.Fatalf("status = %d", rec.Code)
	}
}

func TestWrongMethod(t *testing.T) {
	if rec := do(t, http.MethodGet, "/items", ""); rec.Code != http.StatusMethodNotAllowed {
		t.Fatalf("status = %d", rec.Code)
	}
}

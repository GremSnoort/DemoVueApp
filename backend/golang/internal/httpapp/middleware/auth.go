package middleware

import (
	"context"
	"encoding/json"
	"net/http"
	"strings"

	"demovueapp/backend/internal/auth"
)

type ctxKey string

const (
	CtxUserID  ctxKey = "user_id"
	CtxRole    ctxKey = "role"
	CtxLogin   ctxKey = "login"
)

func writeErrorJSON(w http.ResponseWriter, code int, msg string) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(map[string]any{"error": msg})
}

func Auth(jwt auth.JWTService) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			h := r.Header.Get("Authorization")
			if h == "" || !strings.HasPrefix(h, "Bearer ") {
				writeErrorJSON(w, http.StatusUnauthorized, "missing token")
				return
			}
			token := strings.TrimPrefix(h, "Bearer ")
			claims, err := jwt.Verify(token)
			if err != nil {
				writeErrorJSON(w, http.StatusUnauthorized, "invalid token")
				return
			}
			ctx := context.WithValue(r.Context(), CtxUserID, claims.UserID)
			ctx = context.WithValue(ctx, CtxRole, claims.Role)
			ctx = context.WithValue(ctx, CtxLogin, claims.Login)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

func RequireRole(role string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			got, _ := r.Context().Value(CtxRole).(string)
			if got != role {
				writeErrorJSON(w, http.StatusForbidden, "forbidden")
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}

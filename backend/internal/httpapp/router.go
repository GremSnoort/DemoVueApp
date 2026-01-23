package httpapp

import (
	"net/http"

	"github.com/go-chi/chi/v5"

	"app-template/backend/internal/httpapp/middleware"
)

func (s *Server) Router() http.Handler {
	r := chi.NewRouter()

	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("ok"))
	})

	// Auth
	r.Post("/auth/register", s.Register)
	r.Post("/auth/login", s.Login)

	// Protected
	r.Group(func(pr chi.Router) {
		pr.Use(middleware.Auth(s.jwt))

		pr.Get("/me", s.Me)

		// User requests
		pr.Get("/requests", s.ListMyRequests)
		pr.Post("/requests", s.CreateRequest)
		pr.Post("/requests/{id}/feedback", s.CreateFeedback)

		// Admin
		pr.Group(func(ar chi.Router) {
			ar.Use(middleware.RequireRole("admin"))

			ar.Get("/admin/requests", s.AdminListAllRequests)
			ar.Patch("/admin/requests/{id}/status", s.AdminUpdateRequestStatus)
		})
	})

	return r
}

package httpapp

import (
	"github.com/jackc/pgx/v5/pgxpool"

	"demovueapp/backend/internal/auth"
	"demovueapp/backend/internal/repo"
)

type Server struct {
	jwt auth.JWTService

	users    *repo.UsersRepo
	requests *repo.RequestsRepo
	feedback *repo.FeedbackRepo
	admin    *repo.AdminRepo
}

func NewServer(pool *pgxpool.Pool, jwt auth.JWTService) *Server {
	return &Server{
		jwt:      jwt,
		users:    repo.NewUsersRepo(pool),
		requests: repo.NewRequestsRepo(pool),
		feedback: repo.NewFeedbackRepo(pool),
		admin:    repo.NewAdminRepo(pool),
	}
}

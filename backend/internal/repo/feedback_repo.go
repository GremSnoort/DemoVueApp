package repo

import (
	"context"

	"github.com/jackc/pgx/v5/pgxpool"
)

type FeedbackRepo struct {
	pool *pgxpool.Pool
}

func NewFeedbackRepo(pool *pgxpool.Pool) *FeedbackRepo {
	return &FeedbackRepo{pool: pool}
}

type FeedbackRow struct {
	ID        string  `json:"id"`
	RequestID string  `json:"request_id"`
	UserID    string  `json:"user_id"`
	Rating    int     `json:"rating"`
	Comment   *string `json:"comment,omitempty"`
	CreatedAt string  `json:"created_at"`
}

func (r *FeedbackRepo) Create(ctx context.Context, requestID, userID string, rating int, comment *string) (FeedbackRow, error) {
	var f FeedbackRow
	err := r.pool.QueryRow(ctx, `
		INSERT INTO feedback (request_id, user_id, rating, comment)
		VALUES ($1,$2,$3,$4)
		RETURNING id, request_id, user_id, rating, comment, created_at::text
	`, requestID, userID, rating, comment).
		Scan(&f.ID, &f.RequestID, &f.UserID, &f.Rating, &f.Comment, &f.CreatedAt)
	return f, err
}

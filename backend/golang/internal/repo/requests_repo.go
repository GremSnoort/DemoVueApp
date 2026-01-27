package repo

import (
	"context"
	"encoding/json"
	"errors"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type RequestsRepo struct {
	pool *pgxpool.Pool
}

func NewRequestsRepo(pool *pgxpool.Pool) *RequestsRepo {
	return &RequestsRepo{pool: pool}
}

type RequestRow struct {
	ID           string          `json:"id"`
	UserID       string          `json:"user_id"`
	Type         string          `json:"type"`
	Payload      json.RawMessage `json:"payload"`
	Status       string          `json:"status"`
	AdminComment *string         `json:"admin_comment,omitempty"`
	CreatedAt    string          `json:"created_at"`
	UpdatedAt    string          `json:"updated_at"`
}

func (r *RequestsRepo) Create(ctx context.Context, userID, typ string, payload json.RawMessage) (RequestRow, error) {
	var rr RequestRow
	err := r.pool.QueryRow(ctx, `
		INSERT INTO requests (user_id, type, payload)
		VALUES ($1, $2, $3)
		RETURNING id, user_id, type, payload, status, admin_comment, created_at::text, updated_at::text
	`, userID, typ, payload).
		Scan(&rr.ID, &rr.UserID, &rr.Type, &rr.Payload, &rr.Status, &rr.AdminComment, &rr.CreatedAt, &rr.UpdatedAt)
	return rr, err
}

func (r *RequestsRepo) ListByUser(ctx context.Context, userID string) ([]RequestRow, error) {
	rows, err := r.pool.Query(ctx, `
		SELECT id, user_id, type, payload, status, admin_comment, created_at::text, updated_at::text
		FROM requests
		WHERE user_id=$1
		ORDER BY created_at DESC
	`, userID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []RequestRow
	for rows.Next() {
		var rr RequestRow
		if err := rows.Scan(&rr.ID, &rr.UserID, &rr.Type, &rr.Payload, &rr.Status, &rr.AdminComment, &rr.CreatedAt, &rr.UpdatedAt); err != nil {
			return nil, err
		}
		out = append(out, rr)
	}
	return out, rows.Err()
}

func (r *RequestsRepo) BelongsToUser(ctx context.Context, requestID, userID string) (bool, error) {
	var x int
	err := r.pool.QueryRow(ctx, `SELECT 1 FROM requests WHERE id=$1 AND user_id=$2`, requestID, userID).Scan(&x)
	if errors.Is(err, pgx.ErrNoRows) {
		return false, nil
	}
	if err != nil {
		return false, err
	}
	return true, nil
}

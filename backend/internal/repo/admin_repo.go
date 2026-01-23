package repo

import (
	"context"
	"encoding/json"

	"github.com/jackc/pgx/v5/pgxpool"
)

type AdminRepo struct {
	pool *pgxpool.Pool
}

func NewAdminRepo(pool *pgxpool.Pool) *AdminRepo {
	return &AdminRepo{pool: pool}
}

type AdminRequestRow struct {
	ID           string          `json:"id"`
	UserID       string          `json:"user_id"`
	UserLogin    string          `json:"user_login"`
	Type         string          `json:"type"`
	Payload      json.RawMessage `json:"payload"`
	Status       string          `json:"status"`
	AdminComment *string         `json:"admin_comment,omitempty"`
	CreatedAt    string          `json:"created_at"`
	UpdatedAt    string          `json:"updated_at"`
}

func (r *AdminRepo) ListAll(ctx context.Context) ([]AdminRequestRow, error) {
	rows, err := r.pool.Query(ctx, `
		SELECT req.id, req.user_id, u.login, req.type, req.payload, req.status, req.admin_comment,
		       req.created_at::text, req.updated_at::text
		FROM requests req
		JOIN users u ON u.id = req.user_id
		ORDER BY req.created_at DESC
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []AdminRequestRow
	for rows.Next() {
		var rr AdminRequestRow
		if err := rows.Scan(&rr.ID, &rr.UserID, &rr.UserLogin, &rr.Type, &rr.Payload, &rr.Status, &rr.AdminComment, &rr.CreatedAt, &rr.UpdatedAt); err != nil {
			return nil, err
		}
		out = append(out, rr)
	}
	return out, rows.Err()
}

func (r *AdminRepo) UpdateStatus(ctx context.Context, requestID, status string, adminComment *string) error {
	_, err := r.pool.Exec(ctx, `
		UPDATE requests
		SET status=$2, admin_comment=$3
		WHERE id=$1
	`, requestID, status, adminComment)
	return err
}

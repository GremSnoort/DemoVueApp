package repo

import (
	"context"
	"errors"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type UsersRepo struct {
	pool *pgxpool.Pool
}

func NewUsersRepo(pool *pgxpool.Pool) *UsersRepo {
	return &UsersRepo{pool: pool}
}

type CreateUserParams struct {
	Login        string
	PasswordHash string
	FullName     string
	Phone        string
	Email        string
	Role         string // "user" or "admin"
}

type UserRow struct {
	ID           string
	Login        string
	PasswordHash string
	FullName     string
	Phone        string
	Email        string
	Role         string
}

func (r *UsersRepo) ExistsByLogin(ctx context.Context, login string) (bool, error) {
	var x int
	err := r.pool.QueryRow(ctx, `SELECT 1 FROM users WHERE login=$1`, login).Scan(&x)
	if errors.Is(err, pgx.ErrNoRows) {
		return false, nil
	}
	return err == nil, err
}

func (r *UsersRepo) Create(ctx context.Context, p CreateUserParams) (UserRow, error) {
	var u UserRow
	err := r.pool.QueryRow(ctx, `
		INSERT INTO users (login, password_hash, full_name, phone, email, role)
		VALUES ($1,$2,$3,$4,$5,$6)
		RETURNING id, login, password_hash, full_name, phone, email, role
	`, p.Login, p.PasswordHash, p.FullName, p.Phone, p.Email, p.Role).
		Scan(&u.ID, &u.Login, &u.PasswordHash, &u.FullName, &u.Phone, &u.Email, &u.Role)
	return u, err
}

func (r *UsersRepo) GetByLogin(ctx context.Context, login string) (UserRow, error) {
	var u UserRow
	err := r.pool.QueryRow(ctx, `
		SELECT id, login, password_hash, full_name, phone, email, role
		FROM users WHERE login=$1
	`, login).
		Scan(&u.ID, &u.Login, &u.PasswordHash, &u.FullName, &u.Phone, &u.Email, &u.Role)
	return u, err
}

func (r *UsersRepo) GetByID(ctx context.Context, id string) (UserRow, error) {
	var u UserRow
	err := r.pool.QueryRow(ctx, `
		SELECT id, login, password_hash, full_name, phone, email, role
		FROM users WHERE id=$1
	`, id).
		Scan(&u.ID, &u.Login, &u.PasswordHash, &u.FullName, &u.Phone, &u.Email, &u.Role)
	return u, err
}

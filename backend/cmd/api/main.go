package main

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/cors"
	"github.com/jackc/pgx/v5/pgxpool"

	"app-template/backend/internal/auth"
	"app-template/backend/internal/httpapp"
	"app-template/backend/internal/repo"
)

func main() {
	dsn := os.Getenv("DB_DSN")
	if dsn == "" {
		log.Fatal("DB_DSN is required")
	}
	jwtSecret := os.Getenv("JWT_SECRET")
	if jwtSecret == "" {
		log.Fatal("JWT_SECRET is required")
	}
	adminSeedPassword := os.Getenv("ADMIN_SEED_PASSWORD")
	if adminSeedPassword == "" {
		adminSeedPassword = "Admin12345!"
	}

	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	pool, err := pgxpool.New(ctx, dsn)
	if err != nil {
		log.Fatalf("pgxpool: %v", err)
	}
	defer pool.Close()

	// simple migrations: run SQL file (ok for prototype)
	if err := httpapp.ApplyMigrations(ctx, pool, "migrations"); err != nil {
		log.Fatalf("migrations: %v", err)
	}

	usersRepo := repo.NewUsersRepo(pool)
	if err := seedAdmin(ctx, usersRepo, adminSeedPassword); err != nil {
		log.Fatalf("seed admin: %v", err)
	}

	jwtSvc := auth.NewJWT([]byte(jwtSecret))
	srv := httpapp.NewServer(pool, jwtSvc)

	r := chi.NewRouter()
	r.Use(cors.Handler(cors.Options{
		AllowedOrigins:   []string{"http://localhost:5173"},
		AllowedMethods:   []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type"},
		AllowCredentials: true,
		MaxAge:           300,
	}))
	r.Mount("/api", srv.Router())

	log.Println("Backend listening on :8080")
	if err := http.ListenAndServe(":8080", r); err != nil && !errors.Is(err, http.ErrServerClosed) {
		log.Fatalf("listen: %v", err)
	}
}

func seedAdmin(ctx context.Context, usersRepo *repo.UsersRepo, password string) error {
	// login Admin & password
	const login = "Admin"
	exists, err := usersRepo.ExistsByLogin(ctx, login)
	if err != nil {
		return err
	}
	if exists {
		return nil
	}
	hash, err := auth.HashPassword(password)
	if err != nil {
		return err
	}
	_, err = usersRepo.Create(ctx, repo.CreateUserParams{
		Login:        login,
		PasswordHash: hash,
		FullName:     "Администратор",
		Phone:        "8(000)000-00-00",
		Email:        "admin@example.com",
		Role:         "admin",
	})
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil
		}
		return fmt.Errorf("create admin: %w", err)
	}
	log.Println("Seeded admin user: login=Admin")
	return nil
}

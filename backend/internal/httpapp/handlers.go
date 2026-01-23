package httpapp

import (
	"encoding/json"
	"net/http"
	"regexp"
	"strings"

	"github.com/go-chi/chi/v5"

	"app-template/backend/internal/auth"
	"app-template/backend/internal/httpapp/middleware"
	"app-template/backend/internal/repo"
)

var (
	reLogin    = regexp.MustCompile(`^[A-Za-z0-9]{6,}$`)
	reFullName = regexp.MustCompile(`^[А-Яа-яЁё ]+$`)
	rePhone    = regexp.MustCompile(`^8\(\d{3}\)\d{3}-\d{2}-\d{2}$`)
	reEmail    = regexp.MustCompile(`^[^\s@]+@[^\s@]+\.[^\s@]+$`)
)

func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}

// ---------- AUTH ----------

func (s *Server) Register(w http.ResponseWriter, r *http.Request) {
	type req struct {
		Login    string `json:"login"`
		Password string `json:"password"`
		FullName string `json:"full_name"`
		Phone    string `json:"phone"`
		Email    string `json:"email"`
	}
	var body req
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}

	body.Login = strings.TrimSpace(body.Login)
	body.FullName = strings.TrimSpace(body.FullName)
	body.Phone = strings.TrimSpace(body.Phone)
	body.Email = strings.TrimSpace(body.Email)

	if !reLogin.MatchString(body.Login) {
		http.Error(w, "login must be latin letters/digits, min 6", http.StatusBadRequest)
		return
	}
	if len(body.Password) < 8 {
		http.Error(w, "password min length is 8", http.StatusBadRequest)
		return
	}
	if !reFullName.MatchString(body.FullName) {
		http.Error(w, "full_name must be cyrillic letters and spaces", http.StatusBadRequest)
		return
	}
	if !rePhone.MatchString(body.Phone) {
		http.Error(w, "phone must match 8(XXX)XXX-XX-XX", http.StatusBadRequest)
		return
	}
	if !reEmail.MatchString(body.Email) {
		http.Error(w, "invalid email", http.StatusBadRequest)
		return
	}

	exists, err := s.users.ExistsByLogin(r.Context(), body.Login)
	if err != nil {
		http.Error(w, "db error", http.StatusInternalServerError)
		return
	}
	if exists {
		http.Error(w, "login already exists", http.StatusConflict)
		return
	}

	hash, err := auth.HashPassword(body.Password)
	if err != nil {
		http.Error(w, "hash error", http.StatusInternalServerError)
		return
	}

	u, err := s.users.Create(r.Context(), repo.CreateUserParams{
		Login:        body.Login,
		PasswordHash: hash,
		FullName:     body.FullName,
		Phone:        body.Phone,
		Email:        body.Email,
		Role:         "user",
	})
	if err != nil {
		http.Error(w, "create error", http.StatusInternalServerError)
		return
	}

	writeJSON(w, http.StatusCreated, map[string]any{
		"id": u.ID, "login": u.Login, "full_name": u.FullName, "phone": u.Phone, "email": u.Email, "role": u.Role,
	})
}

func (s *Server) Login(w http.ResponseWriter, r *http.Request) {
	type req struct {
		Login    string `json:"login"`
		Password string `json:"password"`
	}
	var body req
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}

	body.Login = strings.TrimSpace(body.Login)
	if body.Login == "" || body.Password == "" {
		http.Error(w, "login and password required", http.StatusBadRequest)
		return
	}

	u, err := s.users.GetByLogin(r.Context(), body.Login)
	if err != nil {
		http.Error(w, "invalid login or password", http.StatusUnauthorized)
		return
	}
	if !auth.CheckPassword(u.PasswordHash, body.Password) {
		http.Error(w, "invalid login or password", http.StatusUnauthorized)
		return
	}

	token, err := s.jwt.Sign(u.ID, u.Login, u.Role)
	if err != nil {
		http.Error(w, "token error", http.StatusInternalServerError)
		return
	}

	writeJSON(w, http.StatusOK, map[string]any{
		"token": token,
		"user": map[string]any{"id": u.ID, "login": u.Login, "full_name": u.FullName, "role": u.Role},
	})
}

func (s *Server) Me(w http.ResponseWriter, r *http.Request) {
	userID, _ := r.Context().Value(middleware.CtxUserID).(string)
	if userID == "" {
		http.Error(w, "unauthorized", http.StatusUnauthorized)
		return
	}

	u, err := s.users.GetByID(r.Context(), userID)
	if err != nil {
		http.Error(w, "not found", http.StatusNotFound)
		return
	}

	writeJSON(w, http.StatusOK, map[string]any{
		"id": u.ID, "login": u.Login, "full_name": u.FullName, "phone": u.Phone, "email": u.Email, "role": u.Role,
	})
}

// ---------- REQUESTS (USER) ----------

func (s *Server) CreateRequest(w http.ResponseWriter, r *http.Request) {
	userID, _ := r.Context().Value(middleware.CtxUserID).(string)

	type req struct {
		Type    string          `json:"type"`
		Payload json.RawMessage `json:"payload"`
	}
	var body req
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	body.Type = strings.TrimSpace(body.Type)
	if body.Type == "" {
		http.Error(w, "type required", http.StatusBadRequest)
		return
	}
	if len(body.Payload) == 0 {
		body.Payload = []byte(`{}`)
	}

	rr, err := s.requests.Create(r.Context(), userID, body.Type, body.Payload)
	if err != nil {
		http.Error(w, "db error", http.StatusInternalServerError)
		return
	}

	writeJSON(w, http.StatusCreated, rr)
}

func (s *Server) ListMyRequests(w http.ResponseWriter, r *http.Request) {
	userID, _ := r.Context().Value(middleware.CtxUserID).(string)

	items, err := s.requests.ListByUser(r.Context(), userID)
	if err != nil {
		http.Error(w, "db error", http.StatusInternalServerError)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"items": items})
}

// ---------- FEEDBACK ----------

func (s *Server) CreateFeedback(w http.ResponseWriter, r *http.Request) {
	userID, _ := r.Context().Value(middleware.CtxUserID).(string)
	requestID := chi.URLParam(r, "id")

	ok, err := s.requests.BelongsToUser(r.Context(), requestID, userID)
	if err != nil || !ok {
		http.Error(w, "forbidden", http.StatusForbidden)
		return
	}

	type req struct {
		Rating  int     `json:"rating"`
		Comment *string `json:"comment"`
	}
	var body req
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	if body.Rating < 1 || body.Rating > 5 {
		http.Error(w, "rating must be 1..5", http.StatusBadRequest)
		return
	}

	f, err := s.feedback.Create(r.Context(), requestID, userID, body.Rating, body.Comment)
	if err != nil {
		http.Error(w, "db error (maybe feedback already exists)", http.StatusBadRequest)
		return
	}
	writeJSON(w, http.StatusCreated, f)
}

// ---------- ADMIN ----------

func (s *Server) AdminListAllRequests(w http.ResponseWriter, r *http.Request) {
	items, err := s.admin.ListAll(r.Context())
	if err != nil {
		http.Error(w, "db error", http.StatusInternalServerError)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"items": items})
}

func (s *Server) AdminUpdateRequestStatus(w http.ResponseWriter, r *http.Request) {
	requestID := chi.URLParam(r, "id")

	type req struct {
		Status       string  `json:"status"`
		AdminComment *string `json:"admin_comment"`
	}
	var body req
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}

	body.Status = strings.TrimSpace(body.Status)
	switch body.Status {
	case "new", "in_progress", "approved", "rejected", "done":
	default:
		http.Error(w, "invalid status", http.StatusBadRequest)
		return
	}

	if err := s.admin.UpdateStatus(r.Context(), requestID, body.Status, body.AdminComment); err != nil {
		http.Error(w, "db error", http.StatusInternalServerError)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"ok": true})
}

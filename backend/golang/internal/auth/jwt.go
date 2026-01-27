package auth

import (
	"errors"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

type Claims struct {
	UserID string `json:"user_id"`
	Login  string `json:"login"`
	Role   string `json:"role"`
	jwt.RegisteredClaims
}

type JWTService interface {
	Sign(userID, login, role string) (string, error)
	Verify(token string) (*Claims, error)
}

type jwtSvc struct{ secret []byte }

func NewJWT(secret []byte) JWTService { return &jwtSvc{secret: secret} }

func (j *jwtSvc) Sign(userID, login, role string) (string, error) {
	claims := &Claims{
		UserID: userID, Login: login, Role: role,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(24 * time.Hour)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
		},
	}
	t := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return t.SignedString(j.secret)
}

func (j *jwtSvc) Verify(token string) (*Claims, error) {
	t, err := jwt.ParseWithClaims(token, &Claims{}, func(token *jwt.Token) (any, error) {
		return j.secret, nil
	})
	if err != nil {
		return nil, err
	}
	c, ok := t.Claims.(*Claims)
	if !ok || !t.Valid {
		return nil, errors.New("invalid claims")
	}
	return c, nil
}

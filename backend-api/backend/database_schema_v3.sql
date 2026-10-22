-- PostgreSQL schema v3 - API Phát hiện đánh giá sản phẩm giả + Xác thực sản phẩm
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'buyer',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_users_role ON users(role);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    product_code VARCHAR(80) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(150),
    sku VARCHAR(100),
    category VARCHAR(100),
    price DOUBLE PRECISION NOT NULL CHECK (price > 0),
    description TEXT,
    manufacturer VARCHAR(255),
    origin VARCHAR(255),
    batch_number VARCHAR(100),
    production_date DATE,
    expiry_date DATE,
    official_source_url VARCHAR(1000),
    verification_note TEXT,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    verification_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    shop_id INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (expiry_date IS NULL OR production_date IS NULL OR expiry_date >= production_date)
);
CREATE INDEX IF NOT EXISTS ix_products_name ON products(name);
CREATE INDEX IF NOT EXISTS ix_products_product_code ON products(product_code);
CREATE INDEX IF NOT EXISTS ix_products_category ON products(category);
CREATE INDEX IF NOT EXISTS ix_products_shop_id ON products(shop_id);
CREATE INDEX IF NOT EXISTS ix_products_is_verified ON products(is_verified);

CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating DOUBLE PRECISION NOT NULL CHECK (rating >= 1 AND rating <= 5),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_reviews_product_id ON reviews(product_id);
CREATE INDEX IF NOT EXISTS ix_reviews_user_id ON reviews(user_id);

CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    review_id INTEGER NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    predicted_label VARCHAR(20) NOT NULL,
    fake_probability DOUBLE PRECISION NOT NULL CHECK (fake_probability >= 0 AND fake_probability <= 1),
    real_probability DOUBLE PRECISION NOT NULL CHECK (real_probability >= 0 AND real_probability <= 1),
    confidence_score DOUBLE PRECISION NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    explanation TEXT,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_predictions_review_id ON predictions(review_id);
CREATE INDEX IF NOT EXISTS ix_predictions_label_created ON predictions(predicted_label, created_at);

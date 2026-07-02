# Database Schema & API Contracts: 連鎖精品咖啡與甜點品牌 App

**Project**: 6a3e77d4 | **Pipeline**: web-fullstack | **Date**: 2026-07-02

---

## Design Decision (from CEO Ruling)

Per the Brand_Director vs Growth_Hacker debate ruling, the app adopts a **hybrid approach**:
- **70% Minimalist brand-first design** (Blue Bottle style): clean typography, generous whitespace, hero imagery
- **30% Conversion-optimized elements**: subtle promotional cards, seasonal offers integrated tastefully, not aggressively
- Key ruling: "Elevate the brand; let quality and aesthetics drive conversion, not urgency or FOMO."

---

## Database Schema

### Table: `products`

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | Unique product identifier |
| `name_zh` | VARCHAR(128) | NOT NULL | Product name (Traditional Chinese) |
| `name_en` | VARCHAR(128) | NOT NULL | Product name (English) |
| `category` | ENUM('coffee', 'dessert', 'set_menu', 'merchandise') | NOT NULL, INDEX | Product category |
| `description_zh` | TEXT | NOT NULL | Product description (Chinese) |
| `description_en` | TEXT | NOT NULL | Product description (English) |
| `price_twd` | INTEGER | NOT NULL, CHECK(price_twd > 0) | Price in TWD (integer for precision) |
| `image_url` | VARCHAR(512) | NOT NULL | Primary product image |
| `thumbnail_url` | VARCHAR(512) | | Thumbnail for list views |
| `origin` | VARCHAR(128) | | Coffee bean origin / dessert inspiration |
| `roast_level` | ENUM('light', 'medium', 'dark') | | Coffee roast level (nullable for non-coffee) |
| `is_seasonal` | BOOLEAN | DEFAULT FALSE | Seasonal/limited-time flag |
| `is_featured` | BOOLEAN | DEFAULT FALSE | Featured on homepage |
| `display_order` | INTEGER | DEFAULT 0 | Sort order on menu pages |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | |

**Indexes**: `idx_products_category`, `idx_products_featured`, `idx_products_seasonal`

---

### Table: `hero_banners`

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK | Banner identifier |
| `title_zh` | VARCHAR(256) | NOT NULL | Banner headline (Chinese) |
| `title_en` | VARCHAR(256) | NOT NULL | Banner headline (English) |
| `subtitle_zh` | VARCHAR(512) | | Supporting text (Chinese) |
| `subtitle_en` | VARCHAR(512) | | Supporting text (English) |
| `image_url` | VARCHAR(512) | NOT NULL | Full-width banner image |
| `cta_text_zh` | VARCHAR(64) | | Call-to-action (Chinese) |
| `cta_text_en` | VARCHAR(64) | | Call-to-action (English) |
| `cta_link` | VARCHAR(256) | | Deep link target |
| `display_order` | INTEGER | DEFAULT 0 | Carousel ordering |
| `is_active` | BOOLEAN | DEFAULT TRUE | Show/hide toggle |
| `start_date` | DATE | | Campaign start |
| `end_date` | DATE | | Campaign end |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | |

---

### Table: `promotions`

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK | |
| `title_zh` | VARCHAR(128) | NOT NULL | Promo title |
| `title_en` | VARCHAR(128) | NOT NULL | |
| `description_zh` | TEXT | | |
| `description_en` | TEXT | | |
| `discount_type` | ENUM('percentage', 'fixed_amount', 'buy_one_get_one') | NOT NULL | |
| `discount_value` | INTEGER | | e.g. 20 = 20% off or $20 off |
| `product_ids` | UUID[] | | Target products (empty = store-wide) |
| `image_url` | VARCHAR(512) | | Promo card image |
| `is_active` | BOOLEAN | DEFAULT FALSE | |
| `start_date` | TIMESTAMPTZ | NOT NULL | |
| `end_date` | TIMESTAMPTZ | NOT NULL | |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

**Design note**: Promotions are deliberately subtle — no countdown timers, no "LIMITED TIME!" urgency. A single tasteful promo card per homepage view, consistent with the brand-first strategy.

---

### Table: `store_info`

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK | |
| `name_zh` | VARCHAR(256) | NOT NULL | Store/brand name |
| `name_en` | VARCHAR(256) | NOT NULL | |
| `tagline_zh` | VARCHAR(512) | | Brand tagline |
| `tagline_en` | VARCHAR(512) | | |
| `about_zh` | TEXT | | About/brand story |
| `about_en` | TEXT | | |
| `logo_url` | VARCHAR(512) | | Brand logo |
| `primary_color` | VARCHAR(7) | DEFAULT '#2C2C2C' | Brand primary hex |
| `accent_color` | VARCHAR(7) | DEFAULT '#C89B64' | Brand accent hex |
| `background_color` | VARCHAR(7) | DEFAULT '#FAFAFA' | App background |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | |

---

## REST API Contracts

### `GET /api/v1/homepage`

Returns all data needed to render the app homepage.

**Response** (200):
```json
{
  "hero": [
    {
      "id": "uuid",
      "title": "秋季新品·藝伎典藏",
      "title_en": "Autumn Gesha Collection",
      "subtitle": "巴拿馬翡翠莊園·紅標批次",
      "subtitle_en": "Hacienda La Esmeralda · Red Label",
      "image_url": "https://cdn.example.com/hero/autumn-gesha.jpg",
      "cta_text": "探索系列",
      "cta_link": "/products?collection=gesha-autumn"
    }
  ],
  "featured_products": [
    {
      "id": "uuid",
      "name": "藝伎冷萃·限定版",
      "name_en": "Gesha Cold Brew · Limited",
      "category": "coffee",
      "price_twd": 380,
      "image_url": "https://cdn.example.com/products/gesha-coldbrew.jpg",
      "origin": "Panama",
      "roast_level": "light"
    }
  ],
  "promotion": null,
  "categories": [
    {"key": "coffee", "name": "精品咖啡", "name_en": "Specialty Coffee", "icon_url": "..."},
    {"key": "dessert", "name": "手工甜點", "name_en": "Artisan Desserts", "icon_url": "..."},
    {"key": "set_menu", "name": "品味套餐", "name_en": "Tasting Sets", "icon_url": "..."}
  ],
  "brand": {
    "tagline": "一杯咖啡，一種生活態度",
    "tagline_en": "One Cup, One Way of Life",
    "primary_color": "#2C2C2C",
    "accent_color": "#C89B64"
  }
}
```

### `GET /api/v1/products`

Paginated product listing with optional category filter.

**Query params**: `?category=coffee&page=1&page_size=12`

**Response** (200):
```json
{
  "items": [...],
  "total": 48,
  "page": 1,
  "page_size": 12,
  "pages": 4
}
```

### `GET /api/v1/products/{product_id}`

Single product detail. Returns full description, all images, and related products.

### `GET /api/v1/promotions/active`

Returns currently active promotions (at most 1, per brand-first strategy).

**Response** (200):
```json
{
  "promotion": null
}
```

---

## Database Engine
- **Development**: SQLite (`src/ai_embedded_company/storage/`)
- **Production**: PostgreSQL 15+ (matching existing project infrastructure)
- **Migrations**: Alembic (SQLAlchemy-compatible)

## API Framework
- **Backend**: FastAPI (matching existing `src/ai_embedded_company/api/` structure)
- **Validation**: Pydantic v2 models
- **Documentation**: Auto-generated OpenAPI at `/docs`

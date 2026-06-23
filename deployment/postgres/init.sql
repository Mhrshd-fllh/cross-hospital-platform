CREATE TABLE IF NOT EXISTS hospitals (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    location VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inference_requests (
    id UUID PRIMARY KEY, 
    hospital_id INT REFERENCES hospitals(id) ON DELETE RESTRICT,
    image_s3_uri VARCHAR(512) NOT NULL, 
    prediction_label VARCHAR(100), 
    uncertainty_score FLOAT, 
    latency_ms INT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS drift_logs (
    id SERIAL PRIMARY KEY,
    request_id UUID REFERENCES inference_requests(id) ON DELETE CASCADE,
    drift_score FLOAT NOT NULL, 
    status VARCHAR(50) NOT NULL, 
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feedback_logs (
    id SERIAL PRIMARY KEY,
    request_id UUID REFERENCES inference_requests(id) ON DELETE CASCADE UNIQUE,
    is_agreed BOOLEAN NOT NULL, 
    corrected_label VARCHAR(100), 
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_requests_hospital ON inference_requests(hospital_id);
CREATE INDEX IF NOT EXISTS idx_drift_status ON drift_logs(status);
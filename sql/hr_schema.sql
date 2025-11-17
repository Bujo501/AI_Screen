# =========================================
# filepath: AI_Screen/sql/hr_schema.sql  (NEW helper file)
# =========================================
-- Run this once in MySQL Workbench (database: testing1)
CREATE TABLE IF NOT EXISTS hr_role (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  min_years_experience INT NOT NULL DEFAULT 0,
  required_education INT NOT NULL DEFAULT 0,
  description TEXT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS hr_skill (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS hr_role_skill (
  id INT AUTO_INCREMENT PRIMARY KEY,
  role_id INT NOT NULL,
  skill_id INT NOT NULL,
  must_have TINYINT(1) NOT NULL DEFAULT 0,
  weight INT NOT NULL DEFAULT 3,
  CONSTRAINT fk_role FOREIGN KEY (role_id) REFERENCES hr_role(id) ON DELETE CASCADE,
  CONSTRAINT fk_skill FOREIGN KEY (skill_id) REFERENCES hr_skill(id) ON DELETE CASCADE,
  UNIQUE KEY uniq_role_skill (role_id, skill_id, must_have)
) ENGINE=InnoDB;
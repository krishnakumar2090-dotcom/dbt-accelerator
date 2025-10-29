{{ config(materialized='table') }}

WITH vcv_trials AS (
    SELECT
        trial_id AS trial_id, -- Primary key for trial
        UPPER(TRIM(protocol_no)) AS protocol_number, -- Trim spaces, convert to uppercase
        title AS study_title -- Ensure UTF-8 encoding, latest version only
    FROM {{ ref('vcv_trials') }}
),

vcv_sites AS (
    SELECT
        site_id AS site_id -- Composite PK with Trial_ID
    FROM {{ ref('vcv_sites') }}
),

irt_enrollment AS (
    SELECT
        trial_id,
        site_id,
        SUM(subjects_enrolled) AS subject_count, -- Aggregated at trial, site
        planned_subjects AS enrollment_target -- Load as-is
    FROM {{ ref('irt_enrollment') }}
    GROUP BY trial_id, site_id, planned_subjects
)

SELECT
    vcv_trials.trial_id, -- Primary key for trial
    vcv_trials.protocol_number, -- Trimmed and uppercase protocol number
    vcv_trials.study_title, -- Latest version of study title
    vcv_sites.site_id, -- Composite PK with Trial_ID
    irt_enrollment.subject_count, -- Aggregated subject count
    irt_enrollment.enrollment_target -- Planned enrollment target
FROM vcv_trials
LEFT JOIN vcv_sites
    ON vcv_trials.trial_id = vcv_sites.site_id
LEFT JOIN irt_enrollment
    ON vcv_trials.trial_id = irt_enrollment.trial_id
{{ config(materialized='table') }}

WITH vcv_trials_cleaned AS (
    SELECT
        trial_id AS trial_id, -- Primary key for trial
        UPPER(TRIM(protocol_no)) AS protocol_number, -- Protocol number standardized
        title AS study_title -- Study title (latest version only)
    FROM {{ ref('vcv_trials') }}
),

vcv_sites_cleaned AS (
    SELECT
        site_id AS site_id -- Composite PK with trial_id
    FROM {{ ref('vcv_sites') }}
),

irt_enrollment_aggregated AS (
    SELECT
        trial_id,
        site_id,
        SUM(subjects_enrolled) AS subject_count, -- Aggregated subject count
        planned_subjects AS enrollment_target -- Planned enrollment target
    FROM {{ ref('irt_enrollment') }}
    GROUP BY trial_id, site_id, planned_subjects
),

combined_data AS (
    SELECT
        vt.trial_id,
        vt.protocol_number,
        vt.study_title,
        vs.site_id,
        ie.subject_count,
        ie.enrollment_target
    FROM vcv_trials_cleaned vt
    LEFT JOIN vcv_sites_cleaned vs
        ON vt.trial_id = vs.site_id
    LEFT JOIN irt_enrollment_aggregated ie
        ON vt.trial_id = ie.trial_id AND vs.site_id = ie.site_id
)

SELECT
    trial_id, -- Primary key for trial
    protocol_number, -- Standardized protocol number
    study_title, -- Study title (latest version only)
    site_id, -- Composite PK with trial_id
    subject_count, -- Aggregated subject count
    enrollment_target -- Planned enrollment target
FROM combined_data
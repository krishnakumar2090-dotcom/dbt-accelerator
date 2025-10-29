{{ config(materialized='table') }}

WITH vcv_trials_cleaned AS (
    SELECT
        trial_id AS trial_id, -- Primary key for trial
        UPPER(TRIM(protocol_no)) AS protocol_number, -- Trim spaces, convert to uppercase
        title AS study_title -- Ensure UTF-8 encoding, latest version only
    FROM {{ ref('vcv_trials') }}
),

vcv_sites_cleaned AS (
    SELECT
        site_id AS site_id -- Composite PK with Trial_ID
    FROM {{ ref('vcv_sites') }}
),

irt_enrollment_aggregated AS (
    SELECT
        trial_id,
        site_id,
        SUM(subjects_enrolled) AS subject_count, -- Aggregated at trial, site
        planned_subjects AS enrollment_target -- Load as-is
    FROM {{ ref('irt_enrollment') }}
    GROUP BY trial_id, site_id, planned_subjects
)

SELECT
    vt.trial_id, -- Primary key for trial
    vt.protocol_number, -- Trimmed and uppercase protocol number
    vt.study_title, -- Latest version of study title
    vs.site_id, -- Composite PK with Trial_ID
    ie.subject_count, -- Aggregated subject count
    ie.enrollment_target -- Planned enrollment target
FROM vcv_trials_cleaned vt
LEFT JOIN vcv_sites_cleaned vs
    ON vt.trial_id = vs.site_id
LEFT JOIN irt_enrollment_aggregated ie
    ON vt.trial_id = ie.trial_id AND vs.site_id = ie.site_id
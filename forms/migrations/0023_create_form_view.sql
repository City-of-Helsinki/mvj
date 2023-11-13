DROP VIEW IF EXISTS entry_view;
CREATE OR REPLACE VIEW entry_view AS
SELECT
    forms_section.title AS section_name,
    forms_field.label AS field_name,
    forms_entry.value AS entry_value,
    plotsearch_plotsearch.name AS plotseach_name,
    plotsearch_plotsearchtype.name AS plotseachtype_name,
    plotsearch_plotsearchsubtype.name AS plotsearchsubtype_name,
    plotsearch_plotsearch.begin_at AS plotsearch_begin_at,
    plotsearch_plotsearch.end_at AS plotsearch_end_at,
    plotsearch_plotsearch.search_class AS plotsearch_search_class,
    plotsearch_plotsearchstage.name AS plotsearchstage_name,
    leasing_planunit.identifier AS planunit_identifier,
    leasing_planunit.area AS planunit_area,
    leasing_planunit.section_area AS planunit_section_area,
    leasing_planunit.plot_division_identifier AS planunit_plot_division_identifier,
    leasing_planunit.plot_division_date_of_approval AS planunit_plot_division_date_of_approval,
    leasing_planunit.plot_division_effective_date AS planunit_plot_division_effective_date,
    leasing_leaseidentifier.identifier AS reservation_identifier,
    leasing_plotdivisionstate.name AS plot_division_state_name,
    leasing_planunit.detailed_plan_identifier AS planunit_detailed_plan_identifier,
    leasing_planunit.detailed_plan_latest_processing_date AS planunit_detailed_plan_latest_processing_date,
    leasing_planunit.detailed_plan_latest_processing_date_note AS planunit_detailed_plan_latest_processing_date_note,
    leasing_planunittype.name AS planunittype_name,
    leasing_planunitstate.name AS planunitstate_name,
    leasing_planunitintendeduse.name AS planunitintendeduse_name,
    leasing_planunit.plan_unit_status AS planunitstatus_name,
    leasing_customdetailedplan.identifier AS customdetailedplan_identifier,
    leasing_customdetailedplan.area AS customdetailedplan_area,
    leasing_leasearea.area AS customdetailedplan_sectionarea,
    leasing_customdetailedplan.detailed_plan AS customdetailedplan_detailed_plan,
    leasing_customdetailedplan.detailed_plan_latest_processing_date AS customdetailedplan_detailed_plan_latest_processing_date,
    leasing_customdetailedplan.detailed_plan_latest_processing_date_note AS customdetailedplan_detailed_plan_latest_processing_date_note,
    leasing_customdetailedplantype.name AS customdetailedplantype_name,
    leasing_customdetailedplanstate.name AS customdetailedplanstate_name,
    leasing_customdetailedplanintendeduse.name AS customdetailedplanintendeduse_name,
    plotsearch_targetstatus.share_of_rental_indicator AS targetstatus_share_of_rental_indicator,
    plotsearch_targetstatus.share_of_rental_denominator AS targetstatus_share_of_rental_denominator,
    plotsearch_targetstatus.reserved AS targetstatus_reserved,
    plotsearch_targetstatus.added_target_to_applicant AS targetstatus_added_target_to_applicant,
    plotsearch_targetstatus.counsel_date AS targetstatus_counsel_date,
    plotsearch_targetstatus.decline_reason AS targetstatus_decline_reason,
    plotsearch_targetstatus.reservation_conditions AS targetstatus_reservation_conditions,
    leasing_financing.name AS targetstatus_proposed_financing,
    leasing_management.name AS targetstatus_proposed_management,
    leasing_hitas.name AS targetstatus_hitas,
    plotsearch_targetstatus.arguments AS targetstatus_arguments
FROM
    forms_entry
    JOIN forms_field ON forms_entry.field_id = forms_field.id
    JOIN forms_section ON forms_field.section_id = forms_section.id
    JOIN forms_form ON forms_section.form_id = forms_form.id
    JOIN forms_entrysection ON forms_entry.entry_section_id = forms_entrysection.id
    JOIN forms_answer ON forms_entrysection.answer_id = forms_answer.id
    JOIN plotsearch_targetstatus ON plotsearch_targetstatus.answer_id = forms_answer.id
    JOIN plotsearch_plotsearchtarget ON plotsearch_targetstatus.plot_search_target_id = plotsearch_plotsearchtarget.id
    JOIN plotsearch_plotsearch ON plotsearch_plotsearchtarget.plot_search_id = plotsearch_plotsearch.id
    JOIN plotsearch_plotsearchstage ON plotsearch_plotsearch.stage_id = plotsearch_plotsearchstage.id
    JOIN plotsearch_plotsearchsubtype ON plotsearch_plotsearch.subtype_id = plotsearch_plotsearchsubtype.id
    JOIN plotsearch_plotsearchtype ON plotsearch_plotsearchsubtype.plot_search_type_id = plotsearch_plotsearchtype.id
    FULL OUTER JOIN leasing_planunit ON plotsearch_plotsearchtarget.plan_unit_id = leasing_planunit.id
    FULL OUTER JOIN leasing_lease ON plotsearch_plotsearchtarget.reservation_identifier_id = leasing_lease.id
    FULL OUTER JOIN leasing_leaseidentifier ON leasing_lease.identifier_id = leasing_leaseidentifier.id
    FULL OUTER JOIN leasing_plotdivisionstate ON leasing_planunit.plot_division_state_id = leasing_plotdivisionstate.id
    FULL OUTER JOIN leasing_planunittype ON leasing_planunit.plan_unit_type_id = leasing_planunittype.id
    FULL OUTER JOIN leasing_planunitstate ON leasing_planunit.plan_unit_state_id = leasing_planunitstate.id
    FULL OUTER JOIN leasing_planunitintendeduse ON leasing_planunit.plan_unit_intended_use_id = leasing_planunitintendeduse.id
    FULL OUTER JOIN leasing_customdetailedplan ON plotsearch_plotsearchtarget.custom_detailed_plan_id = leasing_customdetailedplan.id
    FULL OUTER JOIN leasing_planunittype leasing_customdetailedplantype ON leasing_customdetailedplan.type_id = leasing_customdetailedplantype.id
    FULL OUTER JOIN leasing_planunitstate leasing_customdetailedplanstate ON leasing_customdetailedplan.state_id = leasing_customdetailedplanstate.id
    FULL OUTER JOIN leasing_planunitintendeduse leasing_customdetailedplanintendeduse ON leasing_customdetailedplan.intended_use_id = leasing_customdetailedplanintendeduse.id
    FULL OUTER JOIN leasing_leasearea ON leasing_customdetailedplan.lease_area_id = leasing_leasearea.id
    FULL OUTER JOIN plotsearch_proposedfinancingmanagement ON plotsearch_proposedfinancingmanagement.target_status_id = plotsearch_targetstatus.id
    FULL OUTER JOIN leasing_financing ON plotsearch_proposedfinancingmanagement.proposed_financing_id = leasing_financing.id
    FULL OUTER JOIN leasing_management ON plotsearch_proposedfinancingmanagement.proposed_management_id = leasing_management.id
    FULL OUTER JOIN leasing_hitas ON plotsearch_proposedfinancingmanagement.hitas_id = leasing_hitas.id
WHERE
    forms_section.visible=TRUE AND
    forms_field.enabled=TRUE;

from typing import Any

STANDARD_ENUMERATIONS: dict[str, tuple[str, list[str]]] = {
    "record_status": ("Record Status", ["Draft", "Active", "Inactive", "Archived"]),
    "governance_status": ("Governance Status", ["Draft", "Submitted", "Approved", "Rejected", "Needs Review"]),
    "criticality": ("Criticality", ["Low", "Medium", "High", "Mission Critical"]),
    "confidence": ("Confidence", ["Unknown", "Low", "Medium", "High", "Confirmed"]),
    "source": ("Source", ["Manual", "Imported", "External authoritative system", "Discovered", "Calculated"]),
    "business_product_lifecycle": ("Business Product Lifecycle", ["Planned", "Active", "Sunset", "Retired"]),
    "capability_maturity": ("Capability Maturity", ["Initial", "Developing", "Defined", "Managed", "Optimized"]),
    "process_automation": ("Process Automation", ["Manual", "Mostly Manual", "Hybrid", "Mostly Automated", "Automated"]),
    "business_process_lifecycle": ("Business Process Lifecycle", ["Planned", "Active", "Changing", "Retiring", "Retired"]),
    "organization_type": ("Organization Type", ["Enterprise", "Division", "Business Unit", "Department", "Team", "External Organization"]),
    "application_lifecycle": ("Application Lifecycle", ["Proposed", "Planned", "Development", "Active", "Tolerated", "Sunset", "Retired"]),
    "fit": ("Fit", ["Poor", "Fair", "Good", "Excellent", "Unknown"]),
    "application_service_lifecycle": ("Application Service Lifecycle", ["Proposed", "Active", "Deprecated", "Retired"]),
    "data_classification": ("Data Classification", ["Public", "Internal", "Confidential", "Restricted"]),
    "technology_lifecycle": ("Technology Lifecycle", ["Emerging", "Current", "Aging", "End of Support", "Retired"]),
    "technology_strategy": ("Technology Strategic Status", ["Adopt", "Strategic", "Tolerate", "Contain", "Migrate", "Retire"]),
    "initiative_status": ("Initiative Status", ["Idea", "Proposed", "Approved", "In Progress", "On Hold", "Completed", "Cancelled"]),
    "delivery_health": ("Delivery Health", ["Green", "Amber", "Red", "Unknown"]),
    "architecture_engagement": ("Architecture Engagement", ["Not Required", "Not Started", "Assessment", "Design", "Review", "Approved", "Exception Required", "Complete"]),
    "principle_status": ("Architecture Principle Status", ["Draft", "Proposed", "Approved", "Deprecated", "Retired"]),
    "decision_status": ("Architecture Decision Status", ["Draft", "Proposed", "Accepted", "Rejected", "Superseded", "Deprecated", "Expired"]),
}


def _field(data_type: str, *, required: bool = False, enum: str | None = None, target: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"type": data_type, "required": required}
    if enum:
        result["enum"] = enum
    if target:
        result["target_object_type"] = target
    return result


STANDARD_OBJECT_TYPES: list[dict[str, Any]] = [
    {"key": "business_product", "name": "Business Product", "domain": "Business", "description": "A product or service offered by the enterprise.", "schema": {"product_type": _field("text"), "business_owner": _field("text"), "customer_segment": _field("text"), "strategic_importance": _field("text"), "lifecycle_stage": _field("select", enum="business_product_lifecycle"), "launch_date": _field("date"), "retirement_date": _field("date")}},
    {"key": "business_capability", "name": "Business Capability", "domain": "Business", "description": "An ability the enterprise requires to achieve outcomes.", "schema": {"capability_level": _field("integer"), "parent_capability": _field("object_reference", target="business_capability"), "business_owner": _field("text"), "maturity": _field("select", enum="capability_maturity"), "target_maturity": _field("select", enum="capability_maturity"), "strategic_importance": _field("text")}},
    {"key": "business_process", "name": "Business Process", "domain": "Business", "description": "A structured business process.", "schema": {"parent_process": _field("object_reference", target="business_process"), "process_owner": _field("text"), "frequency": _field("text"), "business_criticality": _field("select", enum="criticality"), "automation_level": _field("select", enum="process_automation"), "lifecycle_stage": _field("select", enum="business_process_lifecycle")}},
    {"key": "organization", "name": "Organization", "domain": "Business", "description": "An internal or external organizational unit.", "schema": {"organization_type": _field("select", enum="organization_type"), "parent_organization": _field("object_reference", target="organization"), "organization_code": _field("text"), "external_organization": _field("boolean")}},
    {"key": "role", "name": "Role", "domain": "Business", "description": "An architecture or business responsibility role, separate from OpenEA authorization roles.", "schema": {"role_type": _field("text"), "organization": _field("object_reference", target="organization"), "responsibilities": _field("long_text")}},
    {"key": "application", "name": "Application", "domain": "Application", "description": "A deployable or acquired software application relevant to enterprise architecture.", "schema": {"application_type": _field("text"), "business_owner": _field("text"), "technical_owner": _field("text"), "lifecycle_stage": _field("select", enum="application_lifecycle"), "business_fit": _field("select", enum="fit"), "technical_fit": _field("select", enum="fit"), "strategic_fit": _field("select", enum="fit"), "hosting_model": _field("text"), "delivery_model": _field("text"), "vendor": _field("text"), "product_name": _field("text"), "version": _field("text"), "go_live_date": _field("date"), "planned_retirement_date": _field("date"), "actual_retirement_date": _field("date"), "replacement_application": _field("object_reference", target="application"), "rto_hours": _field("decimal"), "rpo_hours": _field("decimal"), "data_classification": _field("select", enum="data_classification"), "internet_facing": _field("boolean")}},
    {"key": "application_service", "name": "Application Service", "domain": "Application", "description": "A logical function exposed or provided by an application.", "schema": {"service_type": _field("text"), "service_owner": _field("text"), "lifecycle_stage": _field("select", enum="application_service_lifecycle"), "availability_requirement": _field("text"), "consumer_type": _field("text")}},
    {"key": "data_object", "name": "Data Object", "domain": "Information", "description": "Logical business information rather than a physical database table.", "schema": {"data_domain": _field("text"), "data_owner": _field("text"), "data_steward_role": _field("object_reference", target="role"), "classification": _field("select", enum="data_classification"), "retention_requirement": _field("text"), "personally_identifiable": _field("boolean"), "regulated": _field("boolean")}},
    {"key": "technology", "name": "Technology", "domain": "Technology", "description": "An architectural technology product or platform, not an operational instance.", "schema": {"technology_category": _field("text"), "vendor": _field("text"), "product": _field("text"), "version": _field("text"), "lifecycle_stage": _field("select", enum="technology_lifecycle"), "strategic_status": _field("select", enum="technology_strategy"), "vendor_support_end": _field("date"), "extended_support_end": _field("date"), "internal_support_end": _field("date"), "replacement_technology": _field("object_reference", target="technology"), "approved_for_new_use": _field("boolean")}},
    {"key": "initiative", "name": "Initiative / Project", "domain": "Change", "description": "A change initiative or project affecting architecture.", "schema": {"initiative_type": _field("text"), "sponsor": _field("text"), "owning_organization": _field("object_reference", target="organization"), "architecture_owner": _field("text"), "status": _field("select", enum="initiative_status"), "start_date": _field("date"), "target_end_date": _field("date"), "actual_end_date": _field("date"), "strategic_priority": _field("text"), "delivery_health": _field("select", enum="delivery_health"), "architecture_engagement_status": _field("select", enum="architecture_engagement")}},
    {"key": "architecture_principle", "name": "Architecture Principle", "domain": "Governance", "description": "A durable principle guiding architecture decisions.", "schema": {"statement": _field("long_text", required=True), "rationale": _field("long_text"), "implications": _field("long_text"), "category": _field("text"), "status": _field("select", enum="principle_status"), "effective_date": _field("date"), "review_date": _field("date"), "owner": _field("text")}},
    {"key": "architecture_decision", "name": "Architecture Decision", "domain": "Governance", "description": "An ADR-style architecture decision.", "schema": {"decision_number": _field("text"), "context": _field("long_text", required=True), "decision": _field("long_text", required=True), "rationale": _field("long_text"), "alternatives_considered": _field("long_text"), "consequences": _field("long_text"), "decision_status": _field("select", enum="decision_status"), "decision_date": _field("date"), "effective_date": _field("date"), "review_date": _field("date"), "decision_owner": _field("text"), "approving_body": _field("text"), "exception_expiration": _field("date")}},
]

STANDARD_RELATIONSHIPS: list[dict[str, Any]] = [
    {"key": "requires", "name": "requires", "inverse": "required by", "rules": [("business_product", "business_capability")]},
    {"key": "realizes", "name": "realizes", "inverse": "realized by", "rules": [("business_process", "business_capability")]},
    {"key": "owns", "name": "owns", "inverse": "owned by", "rules": [("organization", "business_product"), ("organization", "business_capability"), ("organization", "application")]},
    {"key": "performs", "name": "performs", "inverse": "performed by", "rules": [("organization", "business_process")]},
    {"key": "participates_in", "name": "participates in", "inverse": "has participant", "rules": [("role", "business_process")]},
    {"key": "accountable_for", "name": "accountable for", "inverse": "accountable role/organization", "rules": [("role", "business_capability"), ("role", "application"), ("organization", "data_object")]},
    {"key": "supports", "name": "supports", "inverse": "supported by", "rules": [("application", "business_capability"), ("application", "business_process"), ("application_service", "business_process")]},
    {"key": "provides", "name": "provides", "inverse": "provided by", "rules": [("application", "application_service")]},
    {"key": "depends_on", "name": "depends on", "inverse": "depended on by", "rules": [("application", "application"), ("technology", "technology"), ("initiative", "initiative")]},
    {"key": "integrates_with", "name": "integrates with", "inverse": "integrates with", "rules": [("application", "application")], "properties": {"integration_type": _field("text"), "protocol": _field("text"), "direction": _field("text"), "criticality": _field("select", enum="criticality"), "description": _field("long_text"), "data_exchanged": _field("long_text")}},
    {"key": "creates", "name": "creates", "inverse": "created by", "rules": [("application", "data_object")]},
    {"key": "reads", "name": "reads", "inverse": "read by", "rules": [("application", "data_object")]},
    {"key": "updates", "name": "updates", "inverse": "updated by", "rules": [("application", "data_object")]},
    {"key": "system_of_record_for", "name": "system of record for", "inverse": "system of record", "rules": [("application", "data_object")]},
    {"key": "uses", "name": "uses", "inverse": "used by", "rules": [("business_process", "data_object"), ("application", "technology"), ("application_service", "technology")]},
    {"key": "standardizes", "name": "standardizes", "inverse": "standardized by", "rules": [("organization", "technology")]},
    {"key": "changes", "name": "changes", "inverse": "changed by", "rules": [("initiative", "application"), ("initiative", "business_process")]},
    {"key": "introduces", "name": "introduces", "inverse": "introduced by", "rules": [("initiative", "application"), ("initiative", "technology")]},
    {"key": "retires", "name": "retires", "inverse": "retired by", "rules": [("initiative", "application"), ("initiative", "technology")]},
    {"key": "improves", "name": "improves", "inverse": "improved by", "rules": [("initiative", "business_capability")]},
    {"key": "conforms_to", "name": "conforms to", "inverse": "conformed to by", "rules": [("architecture_decision", "architecture_principle"), ("application", "architecture_principle"), ("technology", "architecture_principle")]},
    {"key": "deviates_from", "name": "deviates from", "inverse": "deviated from by", "rules": [("architecture_decision", "architecture_principle"), ("application", "architecture_principle")]},
    {"key": "affects", "name": "affects", "inverse": "affected by", "rules": [("architecture_decision", "application"), ("architecture_decision", "technology"), ("architecture_decision", "business_capability"), ("architecture_decision", "initiative")]},
    {"key": "selects", "name": "selects", "inverse": "selected by", "rules": [("architecture_decision", "technology")]},
    {"key": "supersedes", "name": "supersedes", "inverse": "superseded by", "rules": [("architecture_decision", "architecture_decision")]},
]

from __future__ import annotations

from contextlib import suppress
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.metamodel import ArchitectureObject, ArchitectureRelationship, Tag
from app.models.user import User
from app.services.governance_service import GovernanceService
from app.services.object_service import ObjectService
from app.services.relationship_service import RelationshipService, RelationshipServiceError

DEMO_TAG = "OpenEA Demo"


class DemoDataService:
    """Seed an intentionally imperfect but coherent Northstar Financial repository."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.object_service = ObjectService(db)
        self.relationship_service = RelationshipService(db)

    def seed(self, actor: User) -> dict[str, int]:
        existing = self._demo_objects()
        if existing:
            return {"objects": len(existing), "relationships": self._demo_relationship_count(), "created": 0}

        objects: dict[str, ArchitectureObject] = {}

        def add(key: str, type_key: str, name: str, *, description: str = "", lifecycle: str | None = None,
                criticality: str | None = "Medium", properties: dict[str, object] | None = None,
                review_frequency: str | None = "Annual") -> ArchitectureObject:
            obj = self.object_service.create_object(
                object_type_key=type_key,
                name=name,
                description=description,
                record_status="Active",
                governance_status=None,
                lifecycle_stage=lifecycle,
                criticality=criticality,
                owner_organization_id=None,
                owner_role_id=None,
                source="Manual",
                confidence="High",
                valid_from=None,
                valid_until=None,
                aliases="",
                tags=DEMO_TAG,
                properties=properties or {},
                review_frequency=review_frequency,
                actor=actor,
            )
            objects[key] = obj
            return obj

        # Organizations (5)
        add("org_enterprise", "organization", "Northstar Financial", properties={"organization_type": "Enterprise", "organization_code": "NSF", "external_organization": False})
        add("org_retail", "organization", "Retail Banking", properties={"organization_type": "Business Unit", "organization_code": "RET", "external_organization": False})
        add("org_digital", "organization", "Digital Channels", properties={"organization_type": "Department", "organization_code": "DIG", "external_organization": False})
        add("org_data", "organization", "Enterprise Data", properties={"organization_type": "Department", "organization_code": "DATA", "external_organization": False})
        add("org_vendor", "organization", "Northstar Technology Partners", properties={"organization_type": "External Organization", "organization_code": "NTP", "external_organization": True})

        # Roles (6)
        for key, name, role_type in [
            ("role_business", "Retail Business Owner", "Business Owner"),
            ("role_app", "Digital Application Owner", "Application Owner"),
            ("role_arch", "Enterprise Solution Architect", "Solution Architect"),
            ("role_data", "Customer Data Owner", "Data Owner"),
            ("role_tech", "Platform Technology Owner", "Technology Owner"),
            ("role_process", "Banking Process Owner", "Process Owner"),
        ]:
            add(key, "role", name, properties={"role_type": role_type, "responsibilities": f"Northstar demo responsibility for {role_type}."})

        # Business products (4)
        for key, name in [("prod_checking", "Everyday Checking"), ("prod_savings", "Premier Savings"), ("prod_card", "Northstar Rewards Card"), ("prod_digital", "Digital Banking")]:
            add(key, "business_product", name, lifecycle="Active", properties={"product_type": "Financial Service", "strategic_importance": "High", "lifecycle_stage": "Active"})

        # Capabilities (8)
        capabilities = [
            ("cap_customer", "Customer Management", "Managed", "High"),
            ("cap_acquisition", "Customer Acquisition", "Defined", "High"),
            ("cap_service", "Customer Service", "Managed", "High"),
            ("cap_accounts", "Account Management", "Managed", "High"),
            ("cap_payments", "Payments", "Defined", "High"),
            ("cap_cards", "Card Management", "Developing", "Medium"),
            ("cap_risk", "Fraud & Risk Management", "Defined", "High"),
            ("cap_reporting", "Regulatory Reporting", "Developing", "High"),
        ]
        for key, name, maturity, strategic in capabilities:
            add(key, "business_capability", name, properties={"maturity": maturity, "target_maturity": "Managed", "strategic_importance": strategic})
        objects["cap_acquisition"].properties = {**objects["cap_acquisition"].properties, "parent_capability": objects["cap_customer"].id}
        objects["cap_service"].properties = {**objects["cap_service"].properties, "parent_capability": objects["cap_customer"].id}
        self.db.commit()

        # Processes (10)
        for i, (key, name) in enumerate([
            ("proc_onboard", "Onboard Customer"), ("proc_open", "Open Account"), ("proc_service", "Service Customer"),
            ("proc_payment", "Process Payment"), ("proc_transfer", "Transfer Funds"), ("proc_card", "Issue Card"),
            ("proc_fraud", "Investigate Fraud"), ("proc_close", "Close Account"), ("proc_statement", "Generate Statement"),
            ("proc_report", "Produce Regulatory Report"),
        ]):
            add(key, "business_process", name, lifecycle="Active", properties={"frequency": "Daily", "business_criticality": "High" if i in {3, 4, 6} else "Medium", "automation_level": "Mostly Automated", "lifecycle_stage": "Active"})

        # Technologies (10) -- one deliberately EOL.
        tech_specs = [
            ("tech_java", "Java 21", "Current", "Strategic", None),
            ("tech_pg", "PostgreSQL 17", "Current", "Strategic", None),
            ("tech_rhel", "RHEL 9", "Current", "Strategic", None),
            ("tech_eks", "Amazon EKS", "Current", "Adopt", None),
            ("tech_lambda", "AWS Lambda", "Current", "Adopt", None),
            ("tech_dotnet", ".NET 8", "Current", "Strategic", None),
            ("tech_oracle", "Oracle Database 19c", "Aging", "Migrate", (date.today() + timedelta(days=240)).isoformat()),
            ("tech_python", "Python 2.7", "End of Support", "Retire", "2020-01-01"),
            ("tech_kafka", "Apache Kafka 3", "Current", "Tolerate", None),
            ("tech_windows", "Windows Server 2022", "Current", "Strategic", None),
        ]
        for key, name, lifecycle, strategy, eos in tech_specs:
            props = {"technology_category": "Platform", "vendor": "Northstar Demo Vendor", "product": name, "version": name.split()[-1], "lifecycle_stage": lifecycle, "strategic_status": strategy, "approved_for_new_use": strategy not in {"Migrate", "Retire"}}
            if eos:
                props["vendor_support_end"] = eos
            add(key, "technology", name, lifecycle=lifecycle, criticality="High" if key == "tech_python" else "Medium", properties=props)

        # Applications (12), one mission critical on risky Python 2.7.
        app_specs = [
            ("app_portal", "Customer Portal", "Active", "Mission Critical", "Good", "Fair"),
            ("app_mobile", "Mobile Banking", "Active", "High", "Excellent", "Good"),
            ("app_core", "Core Banking", "Active", "Mission Critical", "Excellent", "Good"),
            ("app_pay", "Payments Hub", "Active", "Mission Critical", "Good", "Good"),
            ("app_crm", "Customer CRM", "Active", "High", "Good", "Fair"),
            ("app_card", "Card Platform", "Active", "High", "Good", "Fair"),
            ("app_fraud", "Fraud Detection", "Active", "Mission Critical", "Excellent", "Good"),
            ("app_dw", "Enterprise Data Warehouse", "Active", "High", "Good", "Fair"),
            ("app_report", "Regulatory Reporting", "Active", "Mission Critical", "Good", "Poor"),
            ("app_legacy", "Legacy Customer Lookup", "Tolerated", "High", "Fair", "Poor"),
            ("app_docs", "Document Management", "Active", "Medium", "Good", "Good"),
            ("app_notify", "Notification Service", "Active", "Medium", "Good", "Good"),
        ]
        for index, (key, name, lifecycle, criticality, business_fit, technical_fit) in enumerate(app_specs):
            props = {"application_type": "Business Application", "lifecycle_stage": lifecycle, "business_fit": business_fit, "technical_fit": technical_fit, "strategic_fit": "Good", "hosting_model": "Cloud" if index % 2 == 0 else "Hybrid", "delivery_model": "Internal", "go_live_date": f"20{16 + index % 8:02d}-01-15", "internet_facing": key in {"app_portal", "app_mobile"}}
            if key == "app_legacy":
                props["planned_retirement_date"] = (date.today() + timedelta(days=180)).isoformat()
            add(key, "application", name, lifecycle=lifecycle, criticality=criticality, properties=props)

        # Application services (15), with deliberate duplicate names.
        for index in range(15):
            name = "Customer Profile Service" if index in {0, 1} else f"Northstar Application Service {index + 1}"
            add(f"svc_{index}", "application_service", name, lifecycle="Active", properties={"service_type": "Business Function", "lifecycle_stage": "Active", "consumer_type": "Application"})

        # Data objects (8), one intentionally without SOR.
        for key, name, classification in [
            ("data_customer", "Customer", "Restricted"), ("data_account", "Account", "Confidential"),
            ("data_payment", "Payment", "Confidential"), ("data_card", "Card", "Restricted"),
            ("data_claim", "Fraud Case", "Restricted"), ("data_employee", "Employee", "Confidential"),
            ("data_product", "Product", "Internal"), ("data_marketing", "Marketing Preference", "Confidential"),
        ]:
            add(key, "data_object", name, properties={"data_domain": "Banking", "classification": classification, "retention_requirement": "7 years", "personally_identifiable": key in {"data_customer", "data_employee", "data_marketing"}, "regulated": classification == "Restricted"})

        # Initiatives (4) with a deliberate collision on Customer Portal.
        for key, name, end_days in [
            ("init_mobile", "Digital Experience Modernization", 365), ("init_cloud", "Cloud Platform Migration", 540),
            ("init_data", "Customer 360 Program", 420), ("init_portal", "Customer Portal Accessibility Upgrade", 180),
        ]:
            add(key, "initiative", name, lifecycle=None, properties={"initiative_type": "Strategic Program", "status": "In Progress", "start_date": date.today().isoformat(), "target_end_date": (date.today() + timedelta(days=end_days)).isoformat(), "strategic_priority": "High", "delivery_health": "Green", "architecture_engagement_status": "Design"})

        # Principles (4)
        for key, name, statement in [
            ("prin_api", "API First", "Business capabilities should be exposed through governed application services."),
            ("prin_cloud", "Cloud Preferred", "New solutions should prefer approved cloud platforms."),
            ("prin_data", "Data Has an Owner", "Critical business data must have explicit accountability."),
            ("prin_lifecycle", "Lifecycle Is Managed", "Technology lifecycle and support horizons must be actively managed."),
        ]:
            add(key, "architecture_principle", name, properties={"statement": statement, "rationale": "Northstar demo governance principle.", "category": "Enterprise Architecture"})

        # Decisions (6), including a supersession pair.
        for index in range(6):
            add(f"dec_{index}", "architecture_decision", f"Northstar Architecture Decision {index + 1}", properties={"context": "Northstar Financial requires an explicit architecture choice.", "decision": f"Adopt demo architecture option {index + 1}.", "rationale": "Demonstrates ADR traceability.", "consequences": "Architecture dependencies must follow this decision."})

        def rel(kind: str, source: str, target: str) -> None:
            with suppress(RelationshipServiceError):
                self.relationship_service.create_relationship(
                    relationship_key=kind,
                    source_object_id=objects[source].id,
                    target_object_id=objects[target].id,
                    actor=actor,
                )

        # Business and application traceability.
        for product, cap in [("prod_checking", "cap_accounts"), ("prod_savings", "cap_accounts"), ("prod_card", "cap_cards"), ("prod_digital", "cap_customer")]:
            rel("requires", product, cap)
        for process, cap in [("proc_onboard", "cap_acquisition"), ("proc_open", "cap_accounts"), ("proc_service", "cap_service"), ("proc_payment", "cap_payments"), ("proc_transfer", "cap_payments"), ("proc_card", "cap_cards"), ("proc_fraud", "cap_risk"), ("proc_report", "cap_reporting")]:
            rel("realizes", process, cap)
        for app, cap in [("app_portal", "cap_customer"), ("app_mobile", "cap_customer"), ("app_core", "cap_accounts"), ("app_pay", "cap_payments"), ("app_crm", "cap_service"), ("app_card", "cap_cards"), ("app_fraud", "cap_risk"), ("app_report", "cap_reporting"), ("app_legacy", "cap_service")]:
            rel("supports", app, cap)
        # Capability single point: Reporting only has app_report.
        for app, tech in [("app_portal", "tech_eks"), ("app_portal", "tech_pg"), ("app_mobile", "tech_eks"), ("app_core", "tech_oracle"), ("app_pay", "tech_java"), ("app_crm", "tech_dotnet"), ("app_card", "tech_windows"), ("app_fraud", "tech_kafka"), ("app_dw", "tech_pg"), ("app_report", "tech_python"), ("app_legacy", "tech_python"), ("app_docs", "tech_rhel")]:
            rel("uses", app, tech)
        for i in range(12):
            rel("provides", app_specs[i % len(app_specs)][0], f"svc_{i}")
        # Systems of record: Marketing Preference deliberately missing; Customer deliberately conflicting.
        for app, data in [("app_core", "data_account"), ("app_pay", "data_payment"), ("app_card", "data_card"), ("app_fraud", "data_claim"), ("app_crm", "data_customer"), ("app_core", "data_customer"), ("app_dw", "data_employee"), ("app_core", "data_product")]:
            rel("system_of_record_for", app, data)
        for initiative, app in [("init_mobile", "app_portal"), ("init_portal", "app_portal"), ("init_cloud", "app_core"), ("init_data", "app_dw")]:
            rel("changes", initiative, app)
        for index in range(4):
            rel("conforms_to", f"dec_{index}", ["prin_api", "prin_cloud", "prin_data", "prin_lifecycle"][index])
        rel("selects", "dec_0", "tech_eks")
        rel("affects", "dec_0", "app_portal")
        governance = GovernanceService(self.db)
        for decision_key in ("dec_4", "dec_5"):
            governance.transition(objects[decision_key], "Proposed", actor)
            governance.transition(objects[decision_key], "Accepted", actor)
        rel("supersedes", "dec_5", "dec_4")
        governance.transition(objects["dec_4"], "Superseded", actor)
        objects["app_legacy"].next_review_date = date.today() - timedelta(days=30)
        self.db.commit()

        return {"objects": len(objects), "relationships": self._demo_relationship_count(), "created": len(objects)}

    def remove(self, actor: User) -> dict[str, int]:
        objects = self._demo_objects()
        object_ids = {obj.id for obj in objects}
        relationships = list(self.db.scalars(select(ArchitectureRelationship).where(ArchitectureRelationship.archived_at.is_(None))).unique().all())
        archived_relationships = 0
        for relationship in relationships:
            if relationship.source_object_id in object_ids or relationship.target_object_id in object_ids:
                self.relationship_service.archive_relationship(relationship, actor=actor)
                archived_relationships += 1
        archived_objects = 0
        for obj in objects:
            self.object_service.archive_object(obj, actor=actor)
            archived_objects += 1
        return {"objects": archived_objects, "relationships": archived_relationships}

    def _demo_objects(self) -> list[ArchitectureObject]:
        return list(
            self.db.scalars(
                select(ArchitectureObject)
                .join(ArchitectureObject.tags)
                .where(Tag.name == DEMO_TAG, ArchitectureObject.archived_at.is_(None))
            ).unique().all()
        )

    def _demo_relationship_count(self) -> int:
        ids = {obj.id for obj in self._demo_objects()}
        if not ids:
            return 0
        return len(list(self.db.scalars(select(ArchitectureRelationship).where(ArchitectureRelationship.archived_at.is_(None), ArchitectureRelationship.source_object_id.in_(ids), ArchitectureRelationship.target_object_id.in_(ids))).all()))

from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from ..enums import EQAResult, EquipmentStatus, LabType, QCStatus
from ..models.laboratory import (
    AnalyzerRegistry,
    CalibrationRecord,
    EQARecord,
    EquipmentRegistry,
    LaboratoryRegistry,
    MaintenanceRecord,
    NationalPanelDefinition,
    NationalReferenceLab,
    NationalTestDefinition,
    QCModRecord,
    ReagentInventory,
)


class LaboratoryGovernanceService:
    def __init__(self, db: Session):
        self.db = db

    def register_lab(
        self,
        lab_code: str,
        name_ar: str,
        lab_type: LabType,
        name_en: str | None = None,
        organization_node_id: int | None = None,
        license_number: str | None = None,
        director_name: str | None = None,
        governorate: str | None = None,
        district: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> LaboratoryRegistry:
        lab = LaboratoryRegistry(
            lab_code=lab_code,
            name_ar=name_ar,
            name_en=name_en,
            lab_type=lab_type,
            organization_node_id=organization_node_id,
            license_number=license_number,
            director_name=director_name,
            governorate=governorate,
            district=district,
            phone=phone,
            email=email,
            metadata_json=metadata_json,
        )
        self.db.add(lab)
        self.db.flush()
        return lab

    def get_lab(self, lab_id: int) -> LaboratoryRegistry | None:
        return self.db.query(LaboratoryRegistry).filter(LaboratoryRegistry.id == lab_id).first()

    def get_lab_by_code(self, lab_code: str) -> LaboratoryRegistry | None:
        return (
            self.db.query(LaboratoryRegistry)
            .filter(LaboratoryRegistry.lab_code == lab_code)
            .first()
        )

    def list_labs(
        self,
        lab_type: LabType | None = None,
        governorate: str | None = None,
        active_only: bool = True,
    ) -> list[LaboratoryRegistry]:
        q = self.db.query(LaboratoryRegistry)
        if lab_type:
            q = q.filter(LaboratoryRegistry.lab_type == lab_type)
        if governorate:
            q = q.filter(LaboratoryRegistry.governorate == governorate)
        if active_only:
            q = q.filter(LaboratoryRegistry.is_active.is_(True))
        return q.order_by(LaboratoryRegistry.name_ar).all()

    def register_equipment(
        self,
        lab_id: int,
        equipment_code: str,
        name_ar: str,
        category: str,
        name_en: str | None = None,
        manufacturer: str | None = None,
        model: str | None = None,
        serial_number: str | None = None,
        installation_date: date | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> EquipmentRegistry:
        equip = EquipmentRegistry(
            lab_id=lab_id,
            equipment_code=equipment_code,
            name_ar=name_ar,
            name_en=name_en,
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
            category=category,
            installation_date=installation_date,
            metadata_json=metadata_json,
        )
        self.db.add(equip)
        self.db.flush()
        return equip

    def register_analyzer(
        self,
        lab_id: int,
        analyzer_code: str,
        name_ar: str,
        analyzer_type: str,
        name_en: str | None = None,
        manufacturer: str | None = None,
        model: str | None = None,
        serial_number: str | None = None,
        test_menu: dict[str, Any] | None = None,
        installation_date: date | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> AnalyzerRegistry:
        analyzer = AnalyzerRegistry(
            lab_id=lab_id,
            analyzer_code=analyzer_code,
            name_ar=name_ar,
            name_en=name_en,
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
            analyzer_type=analyzer_type,
            test_menu=test_menu,
            installation_date=installation_date,
            metadata_json=metadata_json,
        )
        self.db.add(analyzer)
        self.db.flush()
        return analyzer

    def record_maintenance(
        self,
        equipment_id: int,
        maintenance_type: str,
        description: str | None = None,
        performed_by: str | None = None,
        performed_date: date | None = None,
        next_maintenance_date: date | None = None,
        parts_replaced: str | None = None,
        notes: str | None = None,
    ) -> MaintenanceRecord:
        record = MaintenanceRecord(
            equipment_id=equipment_id,
            maintenance_type=maintenance_type,
            description=description,
            performed_by=performed_by,
            performed_date=performed_date or date.today(),
            next_maintenance_date=next_maintenance_date,
            parts_replaced=parts_replaced,
            notes=notes,
        )
        self.db.add(record)
        return record

    def record_calibration(
        self,
        analyzer_id: int,
        calibration_type: str,
        performed_by: str | None = None,
        performed_date: date | None = None,
        next_calibration_date: date | None = None,
        calibrator_lot: str | None = None,
        results: dict[str, Any] | None = None,
        passed: bool | None = None,
        notes: str | None = None,
    ) -> CalibrationRecord:
        record = CalibrationRecord(
            analyzer_id=analyzer_id,
            calibration_type=calibration_type,
            performed_by=performed_by,
            performed_date=performed_date or date.today(),
            next_calibration_date=next_calibration_date,
            calibrator_lot=calibrator_lot,
            results=results,
            passed=passed,
            notes=notes,
        )
        self.db.add(record)
        return record

    def record_qc(
        self,
        lab_id: int,
        test_code: str,
        control_level: str,
        result_value: float,
        analyzer_id: int | None = None,
        control_lot: str | None = None,
        mean: float | None = None,
        sd: float | None = None,
        westgard_rules_violated: list[str] | None = None,
        performed_by: str | None = None,
        notes: str | None = None,
    ) -> QCModRecord:
        deviation = abs(result_value - mean) / sd if mean is not None and sd and sd > 0 else 0
        if westgard_rules_violated:
            status = QCStatus.OUT_OF_CONTROL
        elif deviation > 2:
            status = QCStatus.WARNING
        else:
            status = QCStatus.IN_CONTROL

        record = QCModRecord(
            lab_id=lab_id,
            analyzer_id=analyzer_id,
            test_code=test_code,
            control_level=control_level,
            control_lot=control_lot,
            result_value=result_value,
            mean=mean,
            sd=sd,
            status=status,
            westgard_rules_violated=westgard_rules_violated,
            performed_by=performed_by,
            performed_date=datetime.now(),
            notes=notes,
        )
        self.db.add(record)
        return record

    def record_eqa(
        self,
        lab_id: int,
        test_code: str,
        scheme_name: str,
        round_number: str,
        submitted_result: float | None = None,
        target_value: float | None = None,
        acceptable_range: str | None = None,
        submitted_by: str | None = None,
        corrective_action: str | None = None,
    ) -> EQARecord:
        z_score = None
        deviation_percent = None
        result = None
        if submitted_result is not None and target_value is not None:
            deviation_percent = abs((submitted_result - target_value) / target_value) * 100 if target_value != 0 else None
            if deviation_percent is not None:
                if deviation_percent <= 5:
                    result = EQAResult.ACCEPTABLE
                elif deviation_percent <= 10:
                    result = EQAResult.BORDERLINE
                else:
                    result = EQAResult.UNACCEPTABLE

        record = EQARecord(
            lab_id=lab_id,
            test_code=test_code,
            scheme_name=scheme_name,
            round_number=round_number,
            submitted_result=submitted_result,
            target_value=target_value,
            acceptable_range=acceptable_range,
            z_score=z_score,
            deviation_percent=deviation_percent,
            result=result,
            submitted_by=submitted_by,
            submitted_date=date.today(),
            corrective_action=corrective_action,
        )
        self.db.add(record)
        return record

    def manage_reagent(
        self,
        lab_id: int,
        reagent_code: str,
        reagent_name_ar: str,
        quantity: float,
        unit: str,
        reagent_name_en: str | None = None,
        lot_number: str | None = None,
        manufacturer: str | None = None,
        received_date: date | None = None,
        expiry_date: date | None = None,
        storage_condition: str | None = None,
        minimum_stock_level: float | None = None,
    ) -> ReagentInventory:
        reagent = ReagentInventory(
            lab_id=lab_id,
            reagent_code=reagent_code,
            reagent_name_ar=reagent_name_ar,
            reagent_name_en=reagent_name_en,
            lot_number=lot_number,
            manufacturer=manufacturer,
            quantity=quantity,
            unit=unit,
            received_date=received_date or date.today(),
            expiry_date=expiry_date,
            storage_condition=storage_condition,
            minimum_stock_level=minimum_stock_level,
        )
        self.db.add(reagent)
        return reagent

    def define_national_test(
        self,
        test_code: str,
        name_ar: str,
        category: str,
        name_en: str | None = None,
        department: str | None = None,
        specimen_type: str | None = None,
        loinc_code: str | None = None,
        cpt_code: str | None = None,
        is_national_essential: bool = False,
        tat_target_minutes: int | None = None,
        critical_low: str | None = None,
        critical_high: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> NationalTestDefinition:
        test = NationalTestDefinition(
            test_code=test_code,
            name_ar=name_ar,
            name_en=name_en,
            category=category,
            department=department,
            specimen_type=specimen_type,
            loinc_code=loinc_code,
            cpt_code=cpt_code,
            is_national_essential=is_national_essential,
            tat_target_minutes=tat_target_minutes,
            critical_low=critical_low,
            critical_high=critical_high,
            metadata_json=metadata_json,
        )
        self.db.add(test)
        return test

    def define_national_panel(
        self,
        panel_code: str,
        name_ar: str,
        tests: list[dict[str, Any]],
        name_en: str | None = None,
        category: str | None = None,
    ) -> NationalPanelDefinition:
        panel = NationalPanelDefinition(
            panel_code=panel_code,
            name_ar=name_ar,
            name_en=name_en,
            tests=tests,
            category=category,
        )
        self.db.add(panel)
        return panel

    def designate_reference_lab(
        self,
        lab_id: int,
        reference_domain: str,
        is_national: bool = False,
        is_regional: bool = False,
        designation_date: date | None = None,
        designation_order: str | None = None,
        accredited_standards: list[str] | None = None,
    ) -> NationalReferenceLab:
        ref = NationalReferenceLab(
            lab_id=lab_id,
            reference_domain=reference_domain,
            is_national=is_national,
            is_regional=is_regional,
            designation_date=designation_date or date.today(),
            designation_order=designation_order,
            accredited_standards=accredited_standards,
        )
        self.db.add(ref)
        return ref

    def get_lab_stats(self, lab_id: int) -> dict[str, Any]:
        equip_count = self.db.query(EquipmentRegistry).filter(
            EquipmentRegistry.lab_id == lab_id,
            EquipmentRegistry.status == EquipmentStatus.OPERATIONAL,
        ).count()
        analyzer_count = self.db.query(AnalyzerRegistry).filter(
            AnalyzerRegistry.lab_id == lab_id,
            AnalyzerRegistry.status == "operational",
        ).count()
        eqa_acceptable = self.db.query(EQARecord).filter(
            EQARecord.lab_id == lab_id,
            EQARecord.result == EQAResult.ACCEPTABLE,
        ).count()
        eqa_total = self.db.query(EQARecord).filter(
            EQARecord.lab_id == lab_id,
        ).count()
        qc_in_control = self.db.query(QCModRecord).filter(
            QCModRecord.lab_id == lab_id,
            QCModRecord.status == QCStatus.IN_CONTROL,
        ).count()
        qc_total = self.db.query(QCModRecord).filter(
            QCModRecord.lab_id == lab_id,
        ).count()
        return {
            "lab_id": lab_id,
            "operational_equipment": equip_count,
            "operational_analyzers": analyzer_count,
            "eqa_acceptable_rate": (eqa_acceptable / eqa_total * 100) if eqa_total > 0 else None,
            "qc_in_control_rate": (qc_in_control / qc_total * 100) if qc_total > 0 else None,
            "reagent_count": self.db.query(ReagentInventory).filter(ReagentInventory.lab_id == lab_id).count(),
        }

    def get_low_stock_reagents(self, lab_id: int) -> list[ReagentInventory]:
        return (
            self.db.query(ReagentInventory)
            .filter(
                ReagentInventory.lab_id == lab_id,
                ReagentInventory.minimum_stock_level.isnot(None),
                ReagentInventory.quantity <= ReagentInventory.minimum_stock_level,
            )
            .all()
        )

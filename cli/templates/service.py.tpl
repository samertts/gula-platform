from sqlalchemy.orm import Session

from ..models.{{ model_import }} import {{ class_name }}


class {{ class_name }}Service:
    def __init__(self, db: Session):
        self.db = db

    def list(self, lab_id: int, skip: int = 0, limit: int = 50) -> list[{{ class_name }}]:
        return (
            self.db.query({{ class_name }})
            .filter({{ class_name }}.lab_id == lab_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id(self, id: int, lab_id: int) -> {{ class_name }} | None:
        return self.db.query({{ class_name }}).filter(
            {{ class_name }}.id == id,
            {{ class_name }}.lab_id == lab_id,
        ).first()

    def create(self, lab_id: int, **kwargs) -> {{ class_name }}:
        item = {{ class_name }}(lab_id=lab_id, **kwargs)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, id: int, lab_id: int, **kwargs) -> {{ class_name }} | None:
        item = self.get_by_id(id, lab_id)
        if not item:
            return None
        for key, val in kwargs.items():
            if val is not None:
                setattr(item, key, val)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, id: int, lab_id: int) -> bool:
        item = self.get_by_id(id, lab_id)
        if not item:
            return False
        self.db.delete(item)
        self.db.commit()
        return True

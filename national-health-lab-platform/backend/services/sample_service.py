from models.sample import Sample

def create_sample(db, sample):
    new_sample = Sample(
        patient_id=sample.patient_id,
        sample_type=sample.sample_type,
        status=sample.status
    )

    db.add(new_sample)
    db.commit()
    db.refresh(new_sample)

    return new_sample

def get_samples(db):
    return db.query(Sample).all()

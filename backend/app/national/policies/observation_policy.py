from app.national.policies.base import BasePolicy


class ObservationPolicy(BasePolicy):
    def can_read(self, user, observation):
        user_lab_id = getattr(user, "lab_id", None)
        obs_lab_id = getattr(observation, "lab_id", None)
        if user_lab_id is not None and obs_lab_id is not None:
            return user_lab_id == obs_lab_id
        return True

    def can_write(self, user, patient_id):
        return True

    def can_delete(self, user, observation):
        return self.can_read(user, observation)

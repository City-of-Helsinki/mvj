def user_logged_in(sender, user, **kwargs):
    user.update_service_units()

"""
NoCacheForAuthMiddleware
------------------------
Sets Cache-Control: no-store on every response for authenticated sessions.
This prevents the browser from serving a cached copy of a protected page
after the user has logged out and hits the back button.
"""

class NoCacheForAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Apply no-store to any page served to a logged-in user
        # (covers patient, doctor, and admin sessions)
        is_logged_in = (
            request.session.get('user_id')
            or request.session.get('admin_logged_in')
            or request.session.get('otp_pending_user_id')
        )

        if is_logged_in:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response

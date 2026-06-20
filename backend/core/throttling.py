"""
Morphix â€” Custom Throttling
"""

from rest_framework.throttling import UserRateThrottle, SimpleRateThrottle


class UploadRateThrottle(UserRateThrottle):
    """Rate limit for file uploads."""

    scope = "upload"


class ConversionRateThrottle(UserRateThrottle):
    """Rate limit for file conversions."""

    scope = "conversion"
    rate = "30/minute"


class GuestDailyConversionThrottle(SimpleRateThrottle):
    """Daily rate limit for guest user conversions."""

    scope = "guest_daily"

    def get_cache_key(self, request, view):
        if request.user.is_authenticated and not request.user.is_guest:
            return None
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


class UserDailyConversionThrottle(SimpleRateThrottle):
    """Daily rate limit for registered user conversions."""

    scope = "user_daily"

    def get_cache_key(self, request, view):
        if not request.user.is_authenticated or request.user.is_guest:
            return None
        return self.cache_format % {
            "scope": self.scope,
            "ident": request.user.pk,
        }

class InvalidParameters(Exception):
    """Invalid parameters passed to api.

    .. note::

        No traceback.

    .. admonition:: Example

        When consume api with invalid parameters.
    """

    def __init__(self, message='Invalid Parameters passed to API'):
        super(InvalidParameters, self).__init__(message)
        self.with_traceback(None)
        self.__cause__ = None
        self.traceback = ('', '', '')


class InvalidRefreshToken(Exception):
    """Invalid refresh token.

    .. note::

        No traceback.

    .. admonition:: Example

        When get new access token but refresh token is expired or invalid .
    """

    def __init__(self, message='Refresh token is expired or invalid'):
        super(InvalidRefreshToken, self).__init__(message)
        self.with_traceback(None)
        self.__cause__ = None
        self.traceback = ('', '', '')


class S3ClientError(Exception):
    """Base S3 client exception."""


class S3UploadError(S3ClientError):
    """Raised when upload fails."""


class S3FetchError(S3ClientError):
    """Raised when fetch fails."""


class S3DeleteError(S3ClientError):
    """Raised when delete fails."""


class S3FolderDeleteError(S3ClientError):
    """Raised when folder delete fails."""
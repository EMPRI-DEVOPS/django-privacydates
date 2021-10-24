from hashlib import sha256


def enumeration_key_gen(keystring: str) -> str:
    """Create a reproducable key out of the input string

        Parameters
        ----------
        keystring : String
            The datetime which should be reduced

        Returns
        -------
        String
            sha256 of the input as hex string
        """
    return sha256(str(keystring).encode()).hexdigest()

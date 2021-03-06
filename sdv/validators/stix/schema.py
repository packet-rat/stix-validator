# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# See LICENSE.txt for complete terms.

import os
import common as stix
from sdv import XSD_ROOT
import sdv.errors as errors
import sdv.utils as utils
from sdv.validators import XmlSchemaValidator


class _XmlSchemaValidator(XmlSchemaValidator):
    """Needed to resolve namespace collisions between CybOX 2.1 and
    STIX v1.1.1.

    CybOX imports CPE 2.3. The STIX CVRF extension imports CPE 2.2a. Both
    are defined within the 'http://cpe.mitre.org/language/2.0' namespace.

    """
    OVERRIDE_SCHEMALOC = {
        'http://cpe.mitre.org/language/2.0': os.path.join(
            XSD_ROOT, 'stix_1.1.1', 'cybox', 'external', 'cpe_2.3', 'cpe-language_2.3.xsd'
        )
    }


class STIXSchemaValidator(object):
    SCHEMAS = {
        '1.1.1': os.path.join(XSD_ROOT, 'stix_1.1.1'),
        '1.1': os.path.join(XSD_ROOT, 'stix_1.1'),
        '1.0.1': os.path.join(XSD_ROOT, 'stix_1.0.1'),
        '1.0': os.path.join(XSD_ROOT, 'stix_1.0')
    }

    _KEY_SCHEMALOC = 'schemaloc'
    _KEY_USER_DEFINED = 'user'

    def __init__(self, schema_dir=None):
        self._xml_validators = self._get_validators(schema_dir)
        self._is_user_defined = bool(schema_dir)

    def _get_validators(self, schema_dir=None):
        validators = {self._KEY_SCHEMALOC: _XmlSchemaValidator()}

        if schema_dir:
            validators = {
                self._KEY_USER_DEFINED: _XmlSchemaValidator(schema_dir)
            }
        else:
            for version, location in self.SCHEMAS.iteritems():
                validator = _XmlSchemaValidator(location)
                validators[version] = validator

        return validators

    def _get_version(self, doc):
        try:
            return stix.get_version(doc)
        except KeyError:
            raise errors.UnknownSTIXVersionError(
                "Unable to validate instance document. STIX version not "
                "found in instance document and not supplied to validate() "
                "method"
            )

    def validate(self, doc, version=None, schemaloc=False):
        """Performs XML Schema validation against a STIX document.

        Args:
            doc: The STIX document. This can be a filename, file-like object,
                ``etree._Element``, or ``etree._ElementTree`` instance.
            version: The version of the STIX document. If ``None`` an attempt
                will be made to extract the version from `doc`.
            schemaloc: If ``True``, the ``xsi:schemaLocation`` attribute on
                `doc` will be used to drive the validation.

        Returns:
            An instance of
            :class:`.XmlValidationResults`.

        Raises:
            .UnknownSTIXVersionError: If `version` is ``None`` and
                `doc` does not contain STIX version information.
            .InvalidSTIXVersionError: If `version` is an invalid
                STIX version or `doc` contains an invalid STIX version number.
            .ValidationError: If the class was not initialized with a
                schema directory and `schemaloc` is ``False``.
            .XMLSchemaImportError: If an error occurs while processing the
                schemas required for validation.
            .XMLSchemaIncludeError: If an error occurs while processing
                ``xs:include`` directives.
            .ValidationError: If there are any issues parsing `doc`.

        """
        root = utils.get_etree_root(doc)

        if schemaloc:
            validator = self._xml_validators[self._KEY_SCHEMALOC]
        elif self._is_user_defined:
            validator = self._xml_validators[self._KEY_USER_DEFINED]
        else:
            version = version or self._get_version(doc)
            stix.check_version(version)
            validator = self._xml_validators[version]

        results = validator.validate(root, schemaloc)
        return results


__all__ = [
    'STIXSchemaValidator'
]

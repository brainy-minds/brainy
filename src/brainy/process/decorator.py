from brainy.process import BrainyProcessError


def require_keys_in_description(*description_keys):
    '''
    Apply this decorator to process class if you want to require process
    descriptor to contain particular keys. Notice that this will inject
    respective *property* into the process description.
    '''

    def add_required_property(cls, property_name):
        assert not hasattr(cls, property_name)

        def get_required_description_key(self):
            '''Require process descriptor to contain: %s''' % property_name
            try:
                return self.description[property_name]
            except KeyError:
                raise BrainyProcessError(
                    'Missing "%s" key in JSON descriptor of the process.' %
                    property_name
                )

        setattr(cls, property_name,
                property(fget=get_required_description_key))

    def class_builder(original_class):
        for key in description_keys:
            add_required_property(original_class, key)
        return original_class

    return class_builder


def require_key_in_description(property_method):
    '''
    Same as previous but applicable per property, not class. Make sure
    this decorator is the first to be applied.
    '''

    def get_required_description_key(self):
        property_name = property_method.__name__
        if not property_method.__name__ in self.description:
            raise BrainyProcessError(
                'Missing "%s" key in JSON descriptor of the process.' %
                property_name
            )
        result = property_method(self)
        return self.description[property_name] if result is None else result

    return get_required_description_key


def format_with_params(process_method):
    '''
    Apply this decorator to properties of BrainyProcess() class instances and
    its descendants if you wish to substitute string values of all the
    parameters specified as {variable} using format_with_params().
    '''
    def formatting_with_params(self):
        return self.format_with_params(process_method(self))

    return formatting_with_params

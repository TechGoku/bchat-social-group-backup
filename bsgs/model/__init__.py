from .. import config

if config.PROFANITY_FILTER:
    import better_profanity

    if config.PROFANITY_CUSTOM:
        better_profanity.profanity.load_censor_words_from_file(config.PROFANITY_CUSTOM)
    else:
        better_profanity.profanity.load_censor_words()


# Set of free-form strings that indicate the capability of this bsgs server.  As new features are
# added that a Bchat client might want to know about a string still be added here to allow bchat
# to identify the server's capabilities and act accordingly.
capabilities = {
    'bsgs',  # Basic bsgs capabilities
    # 'newcap',  # Add here
}

if config.REQUIRE_BLIND_KEYS:
    # indicate blinding required if configured to do so
    capabilities.add('blind')

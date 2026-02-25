import click


class DependentOption(click.Option):
    """
    Option that requires one of the dependent options.
    Based on click.Option.
    """

    def __init__(self, *args, depends_on: list[str] = None, **kwargs):
        self.depends_on = depends_on or []
        super().__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        current_value = opts.get(self.name)
        default_value = self.default

        # Check only if flag explicitly changed by user
        if current_value != default_value:
            active_deps = [
                dep for dep in self.depends_on if opts.get(dep) is True
            ]
            blocked_deps = [
                dep
                for dep in self.depends_on
                if opts.get(dep)
                is False  # explicitly got --no-add-equatorial-grid
            ]

            if not active_deps and len(blocked_deps) == len(self.depends_on):
                dep_names = [
                    f"--{d.replace('_', '-')}" for d in self.depends_on
                ]
                raise click.UsageError(
                    f"'--{self.name.replace('_', '-')}' requires "
                    f"one of: {', '.join(dep_names)}."
                )

        return super().handle_parse_result(ctx, opts, args)

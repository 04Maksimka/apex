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
        """
        Check if this option is set, but none of the dependencies are enabled

        :param ctx: param opts:
        :param args: param opts:
        :param opts: 

        """

        current_value = opts.get(self.name)

        if current_value is not None:
            # Convert names: "add_equatorial_grid" -> check value
            active_deps = [
                dep for dep in self.depends_on
                if opts.get(dep) is True
            ]
            if not active_deps:
                dep_names = [f"--{d.replace('_', '-')}" for d in self.depends_on]
                raise click.UsageError(
                    f"'--{self.name.replace('_', '-')}' option requires "
                    f"one of the: {', '.join(dep_names)}."
                )

        return super().handle_parse_result(ctx, opts, args)
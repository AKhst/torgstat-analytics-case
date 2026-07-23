import unittest

from scripts.validate_power_bi_project import validate_measure_formats


class ValidateMeasureFormatsTests(unittest.TestCase):
    def test_column_format_does_not_count_as_measure_format(self) -> None:
        lines = [
            "table Example",
            "",
            "\tcolumn created_at",
            "\t\tdataType: dateTime",
            "\t\tformatString: General Date",
            "",
            "\tpartition Example = m",
        ]
        errors: list[str] = []

        validate_measure_formats("Example.tmdl", lines, errors)

        self.assertEqual(errors, [])

    def test_measure_with_one_format_is_valid(self) -> None:
        lines = [
            "table Example",
            "",
            "\tmeasure 'Metric' = SUM ( Example[value] )",
            "\t\tformatString: #,##0",
            "\t\tdisplayFolder: Metrics",
            "",
            "\tcolumn value",
            "\t\tdataType: int64",
            "\t\tformatString: 0",
        ]
        errors: list[str] = []

        validate_measure_formats("Example.tmdl", lines, errors)

        self.assertEqual(errors, [])

    def test_measure_without_format_reports_measure_name(self) -> None:
        lines = [
            "table Example",
            "",
            "\tmeasure 'Missing Format' = SUM ( Example[value] )",
            "\t\tdisplayFolder: Metrics",
            "",
            "\tcolumn value",
            "\t\tdataType: int64",
        ]
        errors: list[str] = []

        validate_measure_formats("Example.tmdl", lines, errors)

        self.assertEqual(
            errors,
            [
                "Example.tmdl: measure 'Missing Format' must have exactly one "
                "formatString, found 0"
            ],
        )


if __name__ == "__main__":
    unittest.main()

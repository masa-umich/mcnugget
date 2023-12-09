

create_device_channels(ctx)


@pytest.mark.instrument
class TestInstrument:
    def test_valve(self):
        process_valve(
            ctx,
            1,
            {
                DEVICE_COL: "gse",
                ALIAS_COL: "My Valve",
                PORT_COL: 40,
            },
        )

    def test_pt(self):
        with pytest.raises(ValueError):
            process_pt(
                ctx,
                2,
                {
                    DEVICE_COL: "gse",
                    ALIAS_COL: "My PT",
                    PORT_COL: 6000,
                    PT_MAX_PRESSURE_COL: 4000,
                },
            )

    def test_tc(self):
        process_tc(
            ctx,
            3,
            {
                DEVICE_COL: "gse",
                ALIAS_COL: "My TC",
                PORT_COL: 70,
                TC_TYPE_COL: "K",
                TC_OFFSET_COL: 0,
            },
        )

    def test_it_all(self):
        ...

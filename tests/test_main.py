import freeletics


def test_placeholder():
    client = freeletics.FreeleticsClient()
    assert isinstance(client, freeletics.FreeleticsClient)

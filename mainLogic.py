import minescript




def main():

    minescript.echo("Hello test")

    name = minescript.player_name()
    position = minescript.player_position()

    minescript.echo(f"Player: {name}")


if __name__ == "__main__":
    main()


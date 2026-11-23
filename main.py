"""Project Genesis entry point. Physics tests do not require a display."""
import argparse


def main():
    parser=argparse.ArgumentParser(description="PROJECT GENESIS • Laboratório gravitacional 3D")
    parser.add_argument("--smoke-test",type=float,default=0,metavar="SECONDS",
                        help="Fechar automaticamente após N segundos (validação gráfica).")
    parser.add_argument("--verify",action="store_true",help="Validar fluxos e renderizar capturas locais.")
    args=parser.parse_args()
    from visualization.universe import run
    run(args.smoke_test,args.verify)


if __name__=="__main__":
    main()

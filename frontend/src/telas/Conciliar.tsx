/* Tela de entrada da conciliação: o que fazer, em linguagem de estágio. */

import { Botao } from "../componentes/primitivos";

const PASSOS = [
  {
    titulo: "Escolha o mês",
    texto:
      "Toque em Iniciar e selecione no calendário o mês dos relatórios que você tem em mãos. Sem o mês certo, os pagamentos entram no lugar errado.",
  },
  {
    titulo: "Envie os dois relatórios",
    texto:
      "São sempre dois arquivos: o do Itaú (o que o banco pagou) e o de Contas a Pagar (o que a empresa baixou). Os dois juntos montam o histórico de cada pagamento. Um só não basta.",
  },
  {
    titulo: "Atribua conta a quem ainda não tem",
    texto:
      "Alguns fornecedores aparecem sem conta. Para cada um, escolha a conta de débito. Essa escolha vale para os próximos meses, então confira com calma. Se não tiver certeza, pergunte a quem revisa o mês.",
  },
  {
    titulo: "Confera a planilha",
    texto:
      "Olhe favorecido, conta, valor e histórico de cada linha. Se uma linha for diferente das outras do mesmo fornecedor, ajuste só aquela. Não invente regra nova nesta tela.",
  },
  {
    titulo: "Aprove e baixe o arquivo",
    texto:
      "Quando a planilha estiver conferida, aprove o mês e baixe o arquivo para importar no Fortes. Só aprove se estiver seguro: depois disso o mês não se edita mais.",
  },
];

export function Conciliar({
  onIniciar,
}: {
  onIniciar: (origem: { x: number; y: number }) => void;
}) {
  return (
    <div className="conciliar" data-conciliar>
      <header className="tela__cabeca">
        <h1 className="ckp-h2">Como conciliar o mês</h1>
        <p className="ckp-body-sm tela__lede">
          Siga a ordem abaixo, do começo ao fim. Não pule etapa. Se travar,
          volte uma tela e leia de novo o que ela pede.
        </p>
      </header>

      <ol className="conciliar__passos">
        {PASSOS.map((passo) => (
          <li key={passo.titulo}>
            <h2 className="ckp-h4">{passo.titulo}</h2>
            <p className="ckp-body-sm">{passo.texto}</p>
          </li>
        ))}
      </ol>

      <Botao
        tom="primario"
        className="conciliar__iniciar"
        onClick={(e) => {
          const r = e.currentTarget.getBoundingClientRect();
          onIniciar({ x: r.left + r.width / 2, y: r.bottom });
        }}
      >
        Iniciar
      </Botao>
    </div>
  );
}

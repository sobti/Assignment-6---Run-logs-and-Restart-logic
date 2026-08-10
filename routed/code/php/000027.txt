@extends('layouts.app')
@section('content')
<div class="container">
    <div class="row justify-content-center">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">{{ __('Perguntas Respondidas') }}</div>
                <div class="card-body">
                    @if(Session::has('mensagem_sucesso'))
                        <div class="alert alert-success text-center">{{ Session::get('mensagem_sucesso') }}</div>
                    @elseif(Session::has('erro'))
                        <div class="alert alert-danger text-center">{{ Session::get('erro') }}</div>
                    @endif
                    <hr>
                    <table class="table table-bordered" id="dataTable" width="100%" cellspacing="0">
                        <thead>
                            <tr>
                                <th>{{ __('Id') }}</th>
                                <th>{{ __('Nome') }}</th>
                                <th>{{ __('Idade') }}</th>
                                <th>{{ __('Sexo') }}</th>
                                <th>{{ __('ID Pergunta') }}</th>
                                <th>{{ __('ID Resposta') }}</th>
                                <th>{{ __('ID Correta') }}</th>
                                <th>{{ __('Situação') }}</th>
                                <th>{{ __('Data') }}</th>
                            </tr>
                        </thead>
                        <tbody>
                        @if($perguntasRespondidas && count($perguntasRespondidas))
                            @foreach($perguntasRespondidas as $perguntaRespondida)
                                <tr>
                                    <td>{{ $perguntaRespondida->id }}</td>
                                    <td>{{ $perguntaRespondida->nome_pessoa }}</td>
                                    <td>{{ $perguntaRespondida->idade_pessoa }}</td>
                                    <td>{{ $perguntaRespondida->sexo_pessoa }}</td>
                                    <td>{{ $perguntaRespondida->id_pergunta }}</td>
                                    <td>{{ $perguntaRespondida->id_opcao_resposta }}</td>
                                    <td>{{ $perguntaRespondida->id_opcao_correta }}</td>
                                    <td>{{ $perguntaRespondida->situacao }}</td>
                                    <td>{{ $perguntaRespondida->created_at }}</td>
                                </tr>
                            @endforeach
                        @else
                            <tr>
                                <td colspan="5" class="text-center">Nenhuma pergunta respondida.</td>
                            </tr>
                        @endif
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
@endsection




















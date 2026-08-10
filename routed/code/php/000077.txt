@extends('layout')

@section('content')
    <div class="info-container">
        <h1 class="info-title">Stageverslag</h1>
        <h3 class="info-subtitle">1 februari - 1 juni</h3>
        <p class="info-text">Deze periode ga ik stagelopen bij Studio Stomp in Amsterdam, op dit blog ga ik iedere 2 weken een post maken met wat ik die tijd gedaan heb.</p>
        <p class="info-text">Hier vind u alvast de laatste drie weekverslagen, de rest vind u in het weekverslagen overzicht.</p>
    </div>
    <div class="container"> 
    @foreach ($posts as $post)      
         @include('partials/blogpost')
    @endforeach
    </div>
@stop
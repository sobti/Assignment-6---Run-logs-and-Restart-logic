@extends('layouts.emails')
@section('content-emails')
<style>
  button {
 border: none;
 color: #090909;
 padding: 0.7em 1.7em;
 font-size: 18px;
 border-radius: 0.5em;
 background: #e8e8e8;
 border: 1px solid #e8e8e8;
 transition: all .3s;
 box-shadow: 6px 6px 12px #c5c5c5,
             -6px -6px 12px #ffffff;
}
button:active {
 color: #666;
 box-shadow: inset 4px 4px 12px #c5c5c5,
             inset -4px -4px 12px #ffffff;
}
</style>
 <!-- START CENTERED WHITE CONTAINER -->
 <table class="main" style="border-collapse: separate; mso-table-lspace: 0pt; mso-table-rspace: 0pt; width: 100%; background: #ffffff; border-radius: 3px;">
  <!-- START MAIN CONTENT AREA -->
  <tr>
    <td class="wrapper" style="font-family: sans-serif; font-size: 14px; vertical-align: top; box-sizing: border-box; padding: 20px;">


      <table border="0" cellpadding="0" cellspacing="0" style="border-collapse: separate; mso-table-lspace: 0pt; mso-table-rspace: 0pt; width: 100%;">
        <tr>
          <td style="font-family: sans-serif; font-size: 14px; vertical-align: top;">
            <p style="font-family: sans-serif; font-size: 14px; font-weight: normal; margin: 0; Margin-bottom: 15px;">Hi {{$datas->name}},</p>
            <p style="font-family: sans-serif; font-size: 14px; font-weight: normal; margin: 0; Margin-bottom: 15px;">
              You have requested a password change, ignore this Email if you don't make a request.
            </p>
            <br>
            <br>

            <a href="<?php echo $link;?>" target="_blank"><button> Click me</button></a>

            <br>
            <br>
            <p style="font-family: sans-serif; font-size: 14px; font-weight: normal; margin: 0; Margin-bottom: 15px;">
              Copy and paste this link if button not working. <a href="<?php echo $link;?>" target="_blank"><?php echo $link;?></a>
            </p>



          </td>
        </tr>
      </table>


    </td>
  </tr>
<!-- END MAIN CONTENT AREA -->
</table>             
@endsection
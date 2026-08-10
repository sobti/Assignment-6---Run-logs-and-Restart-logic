<?php

/* partials/header_alt.html.twig */
class __TwigTemplate_0eeb3f178a3de2675be9464c77cee9b33dfb2d5dadb512c902ac0ea4596107b5 extends Twig_Template
{
    public function __construct(Twig_Environment $env)
    {
        parent::__construct($env);

        $this->parent = false;

        $this->blocks = array(
        );
    }

    protected function doDisplay(array $context, array $blocks = array())
    {
        // line 1
        echo "
<style type=\"text/css\" id=\"rescue_custom_css\">
.home-header-bg {
  background:url( '";
        // line 4
        echo ($context["theme_url"] ?? null);
        echo "/img/";
        echo $this->getAttribute($this->getAttribute(($context["site"] ?? null), "header", array()), "background", array());
        echo "' ) #ffffff no-repeat center center fixed;
  -webkit-background-size: cover;
  -moz-background-size: cover;
  -o-background-size: cover;
  background-size: cover;
}
/* for background-size:cover replacement on iOS devices */
@media only screen and (max-width: 40em) {
  .home-header-bg {
    background-attachment: scroll;
  }
}
@media only screen and (orientation: portrait) and (device-width: 320px), (device-width: 768px) {
  .home-header-bg {
    -webkit-background-size: auto 150%;
    background-attachment: scroll;
  }
}
@media only screen and (orientation: landscape) and (device-width: 320px), (device-width: 768px) {
  .home-header-bg {
    -webkit-background-size: 150% auto;
    background-attachment: scroll;
  }
}

.bg-image-header {
  background:url( '";
        // line 30
        echo ($context["theme_url"] ?? null);
        echo "/img/";
        echo $this->getAttribute($this->getAttribute(($context["site"] ?? null), "header", array()), "background", array());
        echo "' ) center bottom #ffffff;
  -webkit-background-size: cover;
  -moz-background-size: cover;
  -o-background-size: cover;
  background-size: cover;
  height: 100%;
}

.bg-center-center {
  background-position: center center;
}

.site-branding {
  margin: 0 auto;
  display: table;
  padding-top: 2em;
}
</style>

<div class=\"bg-image bg-image-header bg-center-center\">
  <div class=\"site-branding\">
    <a href=\"";
        // line 51
        echo ($context["base_url_absolute"] ?? null);
        echo "\">
      <img class=\"logo\" src=\"";
        // line 52
        echo ($context["theme_url"] ?? null);
        echo "/img/";
        echo $this->getAttribute(($context["site"] ?? null), "logo", array());
        echo "\" alt=\"";
        echo $this->getAttribute(($context["site"] ?? null), "logo", array());
        echo "\">
    </a>
  </div>
</div>
";
    }

    public function getTemplateName()
    {
        return "partials/header_alt.html.twig";
    }

    public function isTraitable()
    {
        return false;
    }

    public function getDebugInfo()
    {
        return array (  85 => 52,  81 => 51,  55 => 30,  24 => 4,  19 => 1,);
    }

    /** @deprecated since 1.27 (to be removed in 2.0). Use getSourceContext() instead */
    public function getSource()
    {
        @trigger_error('The '.__METHOD__.' method is deprecated since version 1.27 and will be removed in 2.0. Use getSourceContext() instead.', E_USER_DEPRECATED);

        return $this->getSourceContext()->getCode();
    }

    public function getSourceContext()
    {
        return new Twig_Source("
<style type=\"text/css\" id=\"rescue_custom_css\">
.home-header-bg {
  background:url( '{{ theme_url }}/img/{{ site.header.background }}' ) #ffffff no-repeat center center fixed;
  -webkit-background-size: cover;
  -moz-background-size: cover;
  -o-background-size: cover;
  background-size: cover;
}
/* for background-size:cover replacement on iOS devices */
@media only screen and (max-width: 40em) {
  .home-header-bg {
    background-attachment: scroll;
  }
}
@media only screen and (orientation: portrait) and (device-width: 320px), (device-width: 768px) {
  .home-header-bg {
    -webkit-background-size: auto 150%;
    background-attachment: scroll;
  }
}
@media only screen and (orientation: landscape) and (device-width: 320px), (device-width: 768px) {
  .home-header-bg {
    -webkit-background-size: 150% auto;
    background-attachment: scroll;
  }
}

.bg-image-header {
  background:url( '{{ theme_url }}/img/{{ site.header.background }}' ) center bottom #ffffff;
  -webkit-background-size: cover;
  -moz-background-size: cover;
  -o-background-size: cover;
  background-size: cover;
  height: 100%;
}

.bg-center-center {
  background-position: center center;
}

.site-branding {
  margin: 0 auto;
  display: table;
  padding-top: 2em;
}
</style>

<div class=\"bg-image bg-image-header bg-center-center\">
  <div class=\"site-branding\">
    <a href=\"{{ base_url_absolute }}\">
      <img class=\"logo\" src=\"{{ theme_url }}/img/{{ site.logo }}\" alt=\"{{ site.logo }}\">
    </a>
  </div>
</div>
", "partials/header_alt.html.twig", "/Volumes/Dados/workspace/partner-wod.com/user/themes/gateway/templates/partials/header_alt.html.twig");
    }
}

package fr.arthurbr02.player.playerdata;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.databind.ObjectMapper;

@JsonIgnoreProperties(ignoreUnknown = true)
public class PlayerData {
    private Props props;

    public Props getProps() {
        return props;
    }

    public void setProps(Props props) {
        this.props = props;
    }

    public Data getData() {
        return props.getPageProps().getOverallStats().getData();
    }

    public static PlayerData fromHtml(String result, ObjectMapper mapper) {
        try {
            // Il faut récupérer le contenu de la balise script id __NEXT_DATA__ et le parser en JSON
            int scriptStart = result.indexOf("<script id=\"__NEXT_DATA__\" type=\"application/json\">");
            int scriptEnd = result.indexOf("</script>", scriptStart);
            if (scriptStart == -1 || scriptEnd == -1) {
                System.out.println("Script tag not found");
                return null;
            }

            String jsonData = result.substring(
                    scriptStart + "<script id=\"__NEXT_DATA__\" type=\"application/json\">".length(),
                    scriptEnd
            );

            // Maintenant on peut parser jsonData avec Jackson
            return mapper.readValue(jsonData, PlayerData.class);
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }
}

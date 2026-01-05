package fr.arthurbr02.player.playerdata;


import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public class Props {
    private PageProps pageProps;

    public PageProps getPageProps() {
        return pageProps;
    }

    public void setPageProps(PageProps pageProps) {
        this.pageProps = pageProps;
    }
}

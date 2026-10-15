package JsonConfig;
use strict;
use warnings;
use JSON::PP;
use Exporter 'import';

our @EXPORT = qw(load_params);

sub load_params {
    my $file = shift;

    open my $fh, '<', $file or die "Cannot open $file: $!";
    local $/;
    my $p = decode_json(<$fh>);
    close $fh;

    my %flat;
    for my $section (keys %$p) {
        my $entries = $p->{$section};
        next unless ref $entries eq 'HASH';
        for my $key (keys %$entries) {
            my $entry = $entries->{$key};
            next unless ref $entry eq 'HASH' && exists $entry->{value};
            $flat{lc $key} = $entry->{value};
        }
    }

    return \%flat;
}

1;
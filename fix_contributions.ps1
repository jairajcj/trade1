# fix_contributions.ps1
$email = "244541064+jairajcj@users.noreply.github.com"
$name = "jairajcj"

# Configure Git locally
git config user.email $email
git config user.name $name

# Get all commit hashes
$commits = git rev-list --reverse main

$i = 1
foreach ($sha in $commits) {
    # Generate a timestamp for today, staggered by minutes
    $timestamp = (Get-Date).AddMinutes($i).ToString("yyyy-MM-dd HH:mm:ss")
    
    # Update the commit
    $env:GIT_AUTHOR_DATE = $timestamp
    $env:GIT_COMMITTER_DATE = $timestamp
    
    git filter-branch -f --env-filter "
        export GIT_AUTHOR_NAME='$name'
        export GIT_AUTHOR_EMAIL='$email'
        export GIT_COMMITTER_NAME='$name'
        export GIT_COMMITTER_EMAIL='$email'
    " -- $sha^..$sha
    
    $i++
}

# Force push to GitHub
git push origin main --force
